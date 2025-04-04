import requests
import json
from config import Config

class LLMService:
    def __init__(self):
        self.api_url = Config.LLM_API_URL
        self.model = Config.LLM_MODEL
    
    def generate_questions(self, skill_name, num_questions=5, difficulty=3):
        prompt = f"""
        Generate {num_questions} multiple-choice questions about {skill_name} at difficulty level {difficulty}/5.
        Format the response as a JSON array with each question object having:
        - question_text
        - options (array of 4 choices)
        - correct_answer (index of correct option)
        - explanation
        """

        response = self._call_llm(prompt)
        try:
            json_str = self._extract_json(response)
            questions = json.loads(json_str)
            return questions
        except Exception as e:
            print(f"❌ Error parsing LLM response: {e}")
            return []
    
    def assess_proficiency(self, skill_name, user_answers):
        answers_str = "\n".join([f"Q{i+1}: {q['question']}\nUser Answer: {q['user_answer']}\nCorrect Answer: {q['correct_answer']}" 
                              for i, q in enumerate(user_answers)])
        
        prompt = f"""
        The user has answered questions about {skill_name}.
        
        {answers_str}
        
        Based on these answers, assess the user's proficiency level on a scale of 1-5, where:
        1 = Beginner
        2 = Elementary
        3 = Intermediate
        4 = Advanced
        5 = Expert
        
        Provide a proficiency score and a brief explanation of your assessment.
        Format your response as JSON with keys 'score' and 'explanation'.
        """

        response = self._call_llm(prompt)
        try:
            json_str = self._extract_json(response)
            assessment = json.loads(json_str)
            return assessment
        except Exception as e:
            print(f"❌ Error parsing LLM assessment: {e}")
            return {"score": 1, "explanation": "Unable to assess accurately"}
    
    def recommend_resources(self, skill_name, proficiency_level, available_resources):
        resources_str = "\n".join([f"- {r.title} (Level: {r.proficiency_level})" for r in available_resources])

        prompt = f"""
        The user has a proficiency level of {proficiency_level}/5 in {skill_name}.
        
        Available resources:
        {resources_str}
        
        Recommend up to 3 resources that would help the user improve their skills.
        Focus on resources that match their current level or are slightly above.
        Format the response as a JSON array with resource IDs.
        """

        response = self._call_llm(prompt)
        try:
            json_str = self._extract_json(response)
            recommendations = json.loads(json_str)
            return recommendations
        except Exception as e:
            print(f"❌ Error parsing LLM recommendations: {e}")
            return []
    
    def answer_question(self, skill_name, user_question, context=""):
        prompt = f"""
        The user is learning about {skill_name} and has asked the following question:
        
        "{user_question}"
        
        Additional context from learning materials:
        {context}
        
        Provide a helpful, accurate, and concise answer.
        """

        response = self._call_llm(prompt)
        return response

    def _call_llm(self, prompt):
        """Calls the LLM API and shows a loading message while processing."""
        print("🔄 Generating response... Please wait.")  # ✅ Show message before API call

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True  # ✅ Enable streaming if API supports it
        }

        try:
            response = requests.post(self.api_url, json=payload, stream=True)  # ✅ Streaming request

            if response.status_code == 200:
                collected_response = ""

                for chunk in response.iter_lines():
                    if chunk:
                        try:
                            data = json.loads(chunk.decode("utf-8"))
                            collected_response += data.get("response", "")
                        except json.JSONDecodeError:
                            print("⚠️ Warning: Failed to decode chunk:", chunk)

                print("✅ Response generated.")  # ✅ Message after response completes
                return collected_response.strip()

            else:
                print(f"❌ LLM API error: {response.status_code}")
                print(f"Error details: {response.text}")
                return "Error: Unable to process request."

        except Exception as e:
            print(f"❌ Exception when calling LLM API: {str(e)}")
            return "Error: Unable to connect to LLM."

    def _extract_json(self, text):
        """Extracts JSON from text output by the LLM."""
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                return text[start:end]
            
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                return text[start:end]
            
            return "{}"  # Return empty JSON string if no JSON is found
        except Exception as e:
            print(f"❌ Error extracting JSON: {e}")
            return "{}"
