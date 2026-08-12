import os
from typing import List, Dict, Any
from .ai_integration import ai_service

class MultiAgentSystem:
    def __init__(self):
        self.ai = ai_service
        self.prompts = {
            "teaching": "You are ScholarSync's Teaching Agent. You are a personalized AI tutor. Explain programming and academic subjects in detail, provide examples, and create practice tasks. NEVER just give the direct answer; guide the student step-by-step.",
            "career": "You are ScholarSync's Career and Job Training Agent. Analyze user qualifications and interests. Recommend career opportunities, required skills, learning resources, and interview preparation plans.",
            "medical": "You are ScholarSync's Medical Knowledge Agent. Provide educational information about diseases, symptoms, medicines, and healthcare. CRITICAL: You MUST include a disclaimer that you are an AI and the user should consult a qualified medical professional for diagnosis/treatment.",
            "plant": "You are ScholarSync's Plant Intelligence Agent. Analyze the user's questions or images about plants, detect diseases, infections, and provide care methods.",
            "trading": "You are ScholarSync's Trading and Financial Education Agent. Provide educational information about financial concepts, trading, and markets. Include a disclaimer that this is not financial advice.",
            "law": "You are ScholarSync's Law and Police Knowledge Agent. Provide educational information about laws, crimes, legal sections, and police procedures. Include a disclaimer that this is not legal advice."
        }

    def chat(self, agent_type: str, user_message: str, history: List[Any]) -> str:
        system_prompt = self.prompts.get(agent_type, "You are a helpful ScholarSync AI assistant.")
        
        chat_context = ""
        for msg in history:
            role = "USER" if msg.role == "user" else "ASSISTANT"
            chat_context += f"{role}: {msg.content}\n\n"
            
        chat_context += f"USER: {user_message}\n\nASSISTANT:"
        
        res = self.ai.analyze_with_groq(chat_context, system_prompt)
        if res and "error" not in res.lower() and "unauthorized" not in res.lower():
            return res
            
        res2 = self.ai.analyze_with_gemini(f"{system_prompt}\n\n{chat_context}")
        if res2 and "error" not in res2.lower() and "unauthorized" not in res2.lower():
            return res2
            
        return "I am currently offline or experiencing heavy load. Please try again later."

multi_agent_system = MultiAgentSystem()
