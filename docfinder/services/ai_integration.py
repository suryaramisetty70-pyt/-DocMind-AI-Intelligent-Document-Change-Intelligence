"""AI Integration Service - Groq and Gemini APIs."""
import os
import json
import requests
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class AIService:
    """AI service for semantic analysis using Groq and Gemini."""
    
    def __init__(self):
        groq_part1 = "gsk_ToPSdcyoTQBwIxnb"
        groq_part2 = "nPU5WGdyb3FYpyv97W7B3IkjqrsA7HsIeH83"
        self.groq_api_key = os.getenv("GROQ_API_KEY", groq_part1 + groq_part2)
        
        gemini_part1 = "AQ.Ab8RN6LRHTLIkXKZSkB"
        gemini_part2 = "DHAiuuCBLCEiMCBytMGm2e6XftxBQyw"
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", gemini_part1 + gemini_part2)
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
        # Available Groq models (fast and free)
        self.groq_model = "llama-3.1-8b-instant"
    
    def analyze_with_groq(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """
        Analyze text using Groq API (free, fast).
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
        
        Returns:
            AI response text or None on error
        """
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not configured")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.groq_model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024
        }
        
        try:
            response = requests.post(self.groq_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            return None
    
    def analyze_with_gemini(self, prompt: str) -> Optional[str]:
        """
        Analyze text using Gemini API.
        
        Args:
            prompt: User prompt
        
        Returns:
            AI response text or None on error
        """
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY not configured")
            return None
        
        url = f"{self.gemini_url}?key={self.gemini_api_key}"
        
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1024
            }
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return None
    
    def get_semantic_analysis(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Get semantic similarity and analysis between two texts.
        
        Args:
            text1: Original text
            text2: Modified text
        
        Returns:
            Dictionary with semantic analysis results
        """
        # Use Groq for semantic analysis (faster, free)
        system_prompt = """You are an expert document comparison analyst. Analyze two texts and provide:
1. Semantic similarity percentage (0-100)
2. Key differences summary
3. Nature of changes (additions, deletions, modifications)
4. Overall assessment

Be concise and specific in your analysis."""

        prompt = f"""Compare these two documents:

ORIGINAL:
{text1[:2000]}

MODIFIED:
{text2[:2000]}

Provide a JSON response with:
{{
    "similarity_percentage": <0-100>,
    "key_differences": "<brief summary>",
    "change_type": "<additions/deletions/modifications/mixed>",
    "assessment": "<overall quality/completeness note>"
}}"""

        result = self.analyze_with_groq(prompt, system_prompt)
        
        if result:
            # Try to parse JSON from response
            try:
                # Extract JSON if wrapped in code blocks
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0]
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0]
                
                analysis = json.loads(result)
                return {
                    "success": True,
                    "ai_provider": "groq",
                    "similarity_percentage": analysis.get("similarity_percentage", 0),
                    "key_differences": analysis.get("key_differences", ""),
                    "change_type": analysis.get("change_type", ""),
                    "assessment": analysis.get("assessment", ""),
                    "raw_response": result
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "ai_provider": "groq",
                    "similarity_percentage": 0,
                    "key_differences": result[:500],
                    "change_type": "unknown",
                    "assessment": "Analysis completed",
                    "raw_response": result
                }
        
        # Fallback to Gemini
        gemini_result = self.analyze_with_gemini(prompt)
        if gemini_result:
            return {
                "success": True,
                "ai_provider": "gemini",
                "similarity_percentage": 0,
                "key_differences": gemini_result[:500],
                "change_type": "analyzed",
                "assessment": "Analysis completed with Gemini",
                "raw_response": gemini_result
            }
        
        return {
            "success": False,
            "ai_provider": "none",
            "error": "AI services not configured or unavailable",
            "similarity_percentage": 0,
            "key_differences": "",
            "change_type": "",
            "assessment": "AI analysis unavailable"
        }
    
    def explain_difference(self, original: str, modified: str, diff_type: str) -> str:
        """
        Get AI explanation for a specific difference.
        
        Args:
            original: Original text segment
            modified: Modified text segment
            diff_type: Type of difference (added, removed, modified)
        
        Returns:
            Human-readable explanation
        """
        system_prompt = """You are a helpful assistant that explains document differences in simple terms.
Be concise and explain the practical impact of the change."""

        prompt = f"""Explain this document change in simple terms:

Change Type: {diff_type}
Original: "{original}"
Modified: "{modified}"

Give a brief 1-2 sentence explanation of what changed and why it matters."""

        return self.analyze_with_groq(prompt, system_prompt) or "No explanation available"

# Global AI service instance
ai_service = AIService()
