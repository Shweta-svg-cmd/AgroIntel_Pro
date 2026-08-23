# ai_service_free.py - Updated to work with .env
import os
import requests
from datetime import datetime

# ==================== CONFIGURATION ====================
# This will automatically read from .env file
# because we called load_dotenv() in app.py
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

class GroqAIService:
    """FREE AI Service using Groq API - 30 requests/minute"""
    
    def __init__(self, api_key=None):
        # If api_key is provided directly, use it
        # Otherwise, use the one from environment
        self.api_key = api_key or GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "openai/gpt-oss-120b"
        
    # ... rest of the code stays the same ...       
    def get_farm_analysis(self, question, farm_data):
        """Get AI analysis based on farm data and user question"""
        if not self.api_key:
            return {
                'success': False,
                'error': 'Groq API key not set. Please add your API key.',
                'response': self._get_fallback_response(question, farm_data)
            }
        
        context = self._prepare_farm_context(farm_data)
        
        prompt = f"""You are AgroIntel AI, an expert agricultural intelligence assistant. 
You help farmers make data-driven decisions using their farm data.

Here is the farmer's current farm data:
{context}

The farmer asks: {question}

Provide a detailed, actionable response based on the data. 
Include specific recommendations, numbers, and next steps.
Be practical and easy to understand. Format with bullet points and sections."""

        try:
            response = self._call_groq_api(prompt)
            return {
                'success': True,
                'response': response,
                'source': 'Groq AI (FREE)',
                'model': self.model
            }
        except Exception as e:
            error_msg = str(e)
            if "API key" in error_msg:
                return {
                    'success': False,
                    'error': 'Invalid Groq API key. Please check your key.',
                    'response': self._get_fallback_response(question, farm_data)
                }
            else:
                return {
                    'success': False,
                    'error': error_msg,
                    'response': self._get_fallback_response(question, farm_data)
                }
    
    def _call_groq_api(self, prompt):
        """Make API call to Groq"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional agricultural advisor with expertise in precision farming, crop management, and farm optimization. Provide detailed, actionable advice."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 800
        }
        
        response = requests.post(self.api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            error_msg = response.json().get('error', {}).get('message', 'Unknown error')
            raise Exception(f"API Error: {error_msg}")
    
    def _prepare_farm_context(self, data):
        """Prepare farm data for AI context"""
        context_parts = []
        
        context_parts.append(f"Total acres: {data.get('total_acres', 0):.0f}")
        context_parts.append(f"Average yield: {data.get('avg_yield', 0)} t/ha")
        context_parts.append(f"Compliance score: {data.get('compliance_score', 0)}%")
        context_parts.append(f"Active machinery: {data.get('active_machinery', 0)}/{data.get('total_machinery', 0)}")
        
        if data.get('fields'):
            fields_summary = ["Fields:"]
            for field in data['fields']:
                fields_summary.append(
                    f"- {field['name']}: {field['crop']}, {field['acres']} acres, "
                    f"{field['yield']} t/ha, Soil health: {field['soil_health']}%"
                )
            context_parts.extend(fields_summary)
        
        if data.get('machinery'):
            machinery_summary = ["Machinery:"]
            for machine in data['machinery']:
                machinery_summary.append(
                    f"- {machine['name']}: {machine['type']}, {machine['hours']} hours, "
                    f"Fuel: {machine['fuel']}%, Status: {machine['status']}"
                )
            context_parts.extend(machinery_summary)
        
        if data.get('soil'):
            soil_summary = ["Soil Analysis:"]
            for soil in data['soil']:
                soil_summary.append(
                    f"- {soil['field']}: pH {soil['pH']}, N: {soil['nitrogen']}mg/kg, "
                    f"P: {soil['phosphorus']}mg/kg, K: {soil['potassium']}mg/kg"
                )
            context_parts.extend(soil_summary)
        
        if data.get('weather'):
            latest = data['weather'][-1] if data['weather'] else None
            if latest:
                context_parts.append(
                    f"Latest weather: {latest['temperature']}°C, "
                    f"{latest['humidity']}% humidity, "
                    f"{latest['rainfall']}mm rain"
                )
        
        return "\n".join(context_parts)
    
    def _get_fallback_response(self, question, data):
        """Fallback response if API fails"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['crop', 'plant', 'field', 'yield']):
            return self._generate_crop_advice(data)
        elif any(word in question_lower for word in ['machinery', 'tractor', 'maintenance']):
            return self._generate_machinery_advice(data)
        elif any(word in question_lower for word in ['profit', 'money', 'roi']):
            return self._generate_profit_advice(data)
        elif any(word in question_lower for word in ['soil', 'nitrogen', 'fertilizer']):
            return self._generate_soil_advice(data)
        else:
            return self._generate_general_advice(data)
    
    def _generate_crop_advice(self, data):
        fields = data.get('fields', [])
        if not fields:
            return "No fields found. Add fields in Farm Management to get crop advice."
        
        best = max(fields, key=lambda x: x['yield'])
        worst = min(fields, key=lambda x: x['yield'])
        avg_yield = data.get('avg_yield', 0)
        
        return f"""
📊 **Crop Analysis Based on Your Data:**

🌾 **Best Performing Field:** {best['name']}
- Crop: {best['crop']}
- Yield: {best['yield']} t/ha
- Soil Health: {best['soil_health']}%

📉 **Field Needing Attention:** {worst['name']}
- Crop: {worst['crop']}
- Yield: {worst['yield']} t/ha
- Soil Health: {worst['soil_health']}%

💡 **Recommendations:**
- Average yield across all fields: {avg_yield} t/ha
- Focus on improving soil health in {worst['name']}
- Consider crop rotation: If growing corn, rotate with soybeans
- Apply nitrogen fertilizer in spring for best results
"""
    
    def _generate_machinery_advice(self, data):
        machinery = data.get('machinery', [])
        if not machinery:
            return "No machinery found. Add equipment in Machinery section to get advice."
        
        needs_maintenance = [m for m in machinery if m['fuel'] < 30 or m['status'] == 'Maintenance']
        active_count = sum(1 for m in machinery if m['status'] == 'Active')
        
        advice = "🚜 **Machinery Status Report:**\n\n"
        
        if needs_maintenance:
            advice += "⚠️ **Maintenance Required:**\n"
            for m in needs_maintenance:
                if m['fuel'] < 30:
                    advice += f"- {m['name']}: Low fuel ({m['fuel']}%) - Refuel immediately\n"
                if m['status'] == 'Maintenance':
                    advice += f"- {m['name']}: Needs maintenance - Schedule service\n"
        else:
            advice += "✅ All machinery is in good condition!\n"
        
        advice += f"\n📊 **Summary:**\n"
        advice += f"- Total equipment: {len(machinery)}\n"
        advice += f"- Active: {active_count}/{len(machinery)}\n"
        advice += f"- Needs attention: {len(needs_maintenance)}\n"
        
        return advice
    
    def _generate_soil_advice(self, data):
        soil = data.get('soil', [])
        if not soil:
            return "No soil analysis data found. Add soil tests in Soil Analysis section."
        
        advice = "🧪 **Soil Analysis Report:**\n\n"
        
        for s in soil:
            issues = []
            suggestions = []
            
            if s['pH'] < 6.0:
                issues.append(f"Low pH: {s['pH']}")
                suggestions.append("Add lime to raise pH to 6.0-7.0")
            elif s['pH'] > 7.5:
                issues.append(f"High pH: {s['pH']}")
                suggestions.append("Add sulfur to lower pH")
            
            if s['nitrogen'] < 30:
                issues.append(f"Low nitrogen: {s['nitrogen']}mg/kg")
                suggestions.append(f"Apply {48 - s['nitrogen']:.0f} kg/ha nitrogen")
            
            if s['phosphorus'] < 20:
                issues.append(f"Low phosphorus: {s['phosphorus']}mg/kg")
                suggestions.append("Apply phosphorus-rich fertilizer")
            
            if s['potassium'] < 150:
                issues.append(f"Low potassium: {s['potassium']}mg/kg")
                suggestions.append("Apply potassium fertilizer")
            
            if issues:
                advice += f"📍 **{s['field']}:**\n"
                advice += f"- Issues: {', '.join(issues)}\n"
                advice += f"- Recommendations: {', '.join(suggestions)}\n\n"
            else:
                advice += f"✅ **{s['field']}:** All nutrients are optimal!\n\n"
        
        return advice
    
    def _generate_profit_advice(self, data):
        fields = data.get('fields', [])
        if not fields:
            return "Add fields to get profit optimization advice."
        
        total_acres = data.get('total_acres', 0)
        avg_yield = data.get('avg_yield', 0)
        best = max(fields, key=lambda x: x['yield'])
        
        return f"""
💰 **Profit Optimization Analysis:**

📊 **Current Performance:**
- Total acres: {total_acres:.0f}
- Average yield: {avg_yield} t/ha
- Best performing field: {best['name']} ({best['crop']}) - {best['yield']} t/ha

💡 **Recommendations:**
1. Focus on improving lower-yielding fields
2. Consider variable rate application for fertilizer
3. Optimize crop rotation for better yields
4. Monitor input costs vs. yields

📈 **Potential Improvements:**
- Expected ROI increase: 7-11% with optimized practices
- Reduce fertilizer waste with soil testing
- Consider precision agriculture techniques
"""
    
    def _generate_general_advice(self, data):
        fields = data.get('fields', [])
        machinery = data.get('machinery', [])
        
        if not fields and not machinery:
            return """
🌾 **Welcome to AgroIntel!**

You're just getting started. Here's what to do:

1. **Add your fields** → Go to Farm Management
2. **Add your machinery** → Go to Machinery section  
3. **Add soil analysis** → Go to Soil Analysis
4. **Check the Dashboard** → See your farm summary

💡 **Pro Tip:** The more data you add, the better recommendations you'll get!
"""
        
        advice = "🌾 **Farm Overview:**\n\n"
        advice += f"- {len(fields)} fields on {data.get('total_acres', 0):.0f} acres\n"
        advice += f"- {len(machinery)} pieces of equipment\n"
        advice += f"- Compliance Score: {data.get('compliance_score', 0)}%\n"
        
        if fields:
            advice += f"- Average Yield: {data.get('avg_yield', 0)} t/ha\n"
        
        advice += "\n💡 **Next Steps:**\n"
        advice += "- Keep your data updated for better insights\n"
        advice += "- Add soil analysis for fertilizer recommendations\n"
        advice += "- Check the Dashboard regularly for updates\n"
        
        return advice

if __name__ == "__main__":
    print("🤖 Groq AI Service Ready!")