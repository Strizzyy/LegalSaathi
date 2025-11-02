"""
PersonalizationEngine for adaptive response generation based on user experience level
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExperienceLevel(str, Enum):
    """User experience levels for personalized responses"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class PersonalizationEngine:
    """Engine for generating personalized AI responses based on user experience level"""
    
    def __init__(self):
        self.response_templates = self._initialize_templates()
        self.terminology_maps = self._initialize_terminology()
        self.explanation_styles = self._initialize_explanation_styles()
    
    def _initialize_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize response templates for different experience levels"""
        return {
            ExperienceLevel.BEGINNER: {
                "greeting": "I'll explain this in simple terms that are easy to understand.",
                "explanation_intro": "Let me break this down step by step:",
                "risk_intro": "Here's what this could mean for you:",
                "action_intro": "Here's what I recommend you do:",
                "legal_term_intro": "In simple terms, this means:",
                "conclusion": "If you're still unsure, it's always good to ask a lawyer for help."
            },
            ExperienceLevel.INTERMEDIATE: {
                "greeting": "I'll provide a balanced explanation with relevant legal context.",
                "explanation_intro": "Here's what this clause means:",
                "risk_intro": "The potential risks and benefits are:",
                "action_intro": "Consider these options:",
                "legal_term_intro": "This legal concept refers to:",
                "conclusion": "You may want to consult with a legal professional for complex situations."
            },
            ExperienceLevel.EXPERT: {
                "greeting": "Here's a comprehensive legal analysis:",
                "explanation_intro": "Legal analysis:",
                "risk_intro": "Risk assessment and implications:",
                "action_intro": "Strategic considerations:",
                "legal_term_intro": "Legal definition and precedent:",
                "conclusion": "Consider statutory requirements and jurisdictional variations."
            }
        }
    
    def _initialize_terminology(self) -> Dict[str, Dict[str, str]]:
        """Initialize terminology mappings for different experience levels"""
        return {
            ExperienceLevel.BEGINNER: {
                "liability": "responsibility for damages or problems",
                "indemnification": "protection from being sued or having to pay for someone else's mistakes",
                "breach": "breaking the rules of the agreement",
                "termination": "ending the contract",
                "force majeure": "unexpected events (like natural disasters) that make it impossible to fulfill the contract",
                "intellectual property": "ownership of ideas, designs, or creative work",
                "liquidated damages": "a pre-agreed amount of money you'd have to pay if you break the contract",
                "arbitration": "solving disputes through a private judge instead of going to court",
                "governing law": "which state or country's laws apply to this contract",
                "severability": "if one part of the contract is invalid, the rest still applies"
            },
            ExperienceLevel.INTERMEDIATE: {
                "liability": "legal responsibility for damages, losses, or obligations",
                "indemnification": "contractual protection requiring one party to compensate another for specified losses",
                "breach": "failure to perform contractual obligations as specified",
                "termination": "formal ending of contractual relationship with specified procedures",
                "force majeure": "unforeseeable circumstances preventing contract performance",
                "intellectual property": "legally protected intangible assets including patents, trademarks, and copyrights",
                "liquidated damages": "predetermined compensation for breach, enforceable if reasonable",
                "arbitration": "alternative dispute resolution through binding private adjudication",
                "governing law": "jurisdictional law that governs contract interpretation and enforcement",
                "severability": "doctrine preserving contract validity despite invalid provisions"
            },
            ExperienceLevel.EXPERT: {
                "liability": "legal obligation to compensate for damages arising from breach, tort, or statutory violation",
                "indemnification": "contractual risk allocation mechanism requiring indemnitor to hold harmless and defend indemnitee",
                "breach": "material failure to perform contractual obligations constituting grounds for remedies",
                "termination": "contract dissolution through expiration, mutual agreement, or breach with cure period provisions",
                "force majeure": "supervening impossibility doctrine excusing performance due to unforeseeable events",
                "intellectual property": "bundle of exclusive rights in intangible property subject to registration and common law protection",
                "liquidated damages": "pre-estimated damages clause enforceable under penalty doctrine limitations",
                "arbitration": "binding ADR mechanism governed by FAA with limited judicial review",
                "governing law": "choice of law provision determining applicable substantive and procedural rules",
                "severability": "savings clause preserving contract enforceability through blue-pencil doctrine application"
            }
        }
    
    def _initialize_explanation_styles(self) -> Dict[str, Dict[str, Any]]:
        """Initialize explanation styles for different experience levels"""
        return {
            ExperienceLevel.BEGINNER: {
                "use_analogies": True,
                "include_examples": True,
                "step_by_step": True,
                "avoid_jargon": True,
                "max_sentence_length": 20,
                "include_definitions": True,
                "use_bullet_points": True,
                "practical_focus": True
            },
            ExperienceLevel.INTERMEDIATE: {
                "use_analogies": False,
                "include_examples": True,
                "step_by_step": False,
                "avoid_jargon": False,
                "max_sentence_length": 30,
                "include_definitions": False,
                "use_bullet_points": False,
                "practical_focus": True
            },
            ExperienceLevel.EXPERT: {
                "use_analogies": False,
                "include_examples": False,
                "step_by_step": False,
                "avoid_jargon": False,
                "max_sentence_length": 50,
                "include_definitions": False,
                "use_bullet_points": False,
                "practical_focus": False
            }
        }
    
    def personalize_prompt(self, base_prompt: str, experience_level: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Personalize a prompt based on user experience level
        
        Args:
            base_prompt: The base prompt to personalize
            experience_level: User's experience level (beginner/intermediate/expert)
            context: Additional context for personalization
            
        Returns:
            Personalized prompt string
        """
        try:
            level = ExperienceLevel(experience_level.lower())
        except ValueError:
            logger.warning(f"Invalid experience level: {experience_level}, defaulting to beginner")
            level = ExperienceLevel.BEGINNER
        
        templates = self.response_templates[level]
        style = self.explanation_styles[level]
        
        # Build personalized prompt
        personalized_prompt = f"{templates['greeting']}\n\n"
        personalized_prompt += base_prompt
        
        # Add experience-specific instructions
        personalized_prompt += f"\n\nResponse Guidelines for {level.value} level:\n"
        
        if level == ExperienceLevel.BEGINNER:
            personalized_prompt += """
- Use simple, everyday language
- Explain legal terms in plain English
- Provide step-by-step explanations
- Include practical examples and analogies
- Focus on what this means for the person
- Suggest when to get professional help
- Keep sentences short and clear
- Use bullet points for clarity
"""
        elif level == ExperienceLevel.INTERMEDIATE:
            personalized_prompt += """
- Use balanced technical and plain language
- Provide contextual legal explanations
- Include relevant examples when helpful
- Focus on practical implications and options
- Explain risks and benefits clearly
- Suggest professional consultation for complex issues
- Organize information logically
"""
        else:  # EXPERT
            personalized_prompt += """
- Use precise legal terminology
- Provide comprehensive analysis
- Include statutory and case law references where relevant
- Focus on legal implications and strategic considerations
- Address jurisdictional variations
- Provide detailed risk assessment
- Include compliance and regulatory considerations
"""
        
        # Add context-specific personalization
        if context:
            risk_level = context.get('risk_level', 'unknown')
            if risk_level == 'RED' and level == ExperienceLevel.BEGINNER:
                personalized_prompt += "\nIMPORTANT: This is a high-risk area. Explain clearly why this is concerning and strongly recommend professional legal review."
            elif risk_level == 'RED' and level == ExperienceLevel.EXPERT:
                personalized_prompt += "\nNOTE: High-risk clause identified. Provide detailed risk analysis and mitigation strategies."
        
        return personalized_prompt
    
    def personalize_response(self, response: str, experience_level: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Post-process a response to match experience level
        
        Args:
            response: The AI-generated response
            experience_level: User's experience level
            context: Additional context for personalization
            
        Returns:
            Personalized response string
        """
        try:
            level = ExperienceLevel(experience_level.lower())
        except ValueError:
            level = ExperienceLevel.BEGINNER
        
        # Replace legal terms with appropriate explanations
        personalized_response = self._replace_legal_terms(response, level)
        
        # Add experience-appropriate formatting
        personalized_response = self._format_for_experience_level(personalized_response, level)
        
        # Add appropriate conclusion
        templates = self.response_templates[level]
        if not personalized_response.endswith('.'):
            personalized_response += '.'
        
        personalized_response += f"\n\n{templates['conclusion']}"
        
        return personalized_response
    
    def _replace_legal_terms(self, text: str, level: ExperienceLevel) -> str:
        """Replace legal terms with experience-appropriate explanations"""
        terminology = self.terminology_maps[level]
        
        # Only replace terms for beginner level to avoid over-explanation
        if level == ExperienceLevel.BEGINNER:
            for term, explanation in terminology.items():
                # Replace term with explanation in parentheses
                text = text.replace(term, f"{term} ({explanation})")
        
        return text
    
    def _format_for_experience_level(self, text: str, level: ExperienceLevel) -> str:
        """Format text according to experience level preferences"""
        style = self.explanation_styles[level]
        
        if level == ExperienceLevel.BEGINNER and style["use_bullet_points"]:
            # Convert long paragraphs to bullet points for better readability
            sentences = text.split('. ')
            if len(sentences) > 3:
                formatted_text = sentences[0] + '.\n\nKey points:\n'
                for sentence in sentences[1:]:
                    if sentence.strip():
                        formatted_text += f"• {sentence.strip()}\n"
                return formatted_text.rstrip()
        
        return text
    
    def get_experience_level_context(self, experience_level: str) -> Dict[str, Any]:
        """
        Get context information for a specific experience level
        
        Args:
            experience_level: User's experience level
            
        Returns:
            Dictionary containing experience level context
        """
        try:
            level = ExperienceLevel(experience_level.lower())
        except ValueError:
            level = ExperienceLevel.BEGINNER
        
        return {
            "level": level.value,
            "templates": self.response_templates[level],
            "style": self.explanation_styles[level],
            "terminology_count": len(self.terminology_maps[level])
        }
    
    def validate_experience_level(self, experience_level: str) -> bool:
        """
        Validate if the provided experience level is valid
        
        Args:
            experience_level: Experience level to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            ExperienceLevel(experience_level.lower())
            return True
        except ValueError:
            return False
    
    def get_supported_levels(self) -> List[str]:
        """
        Get list of supported experience levels
        
        Returns:
            List of supported experience level strings
        """
        return [level.value for level in ExperienceLevel]