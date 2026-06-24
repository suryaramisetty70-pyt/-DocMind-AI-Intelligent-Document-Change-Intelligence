"""Text comparison engine."""
from typing import List, Dict, Tuple, Any
import difflib


class TextComparisonEngine:
    """Engine for comparing text documents at various levels."""

    @staticmethod
    def compare_text(text1: str, text2: str, level: str = "word") -> Dict[str, Any]:
        """
        Compare two texts and return differences.
        
        Args:
            text1: Original text
            text2: Modified text
            level: Comparison level - 'character', 'word', 'sentence', 'paragraph'
        
        Returns:
            Dictionary with comparison results
        """
        if level == "character":
            return TextComparisonEngine._compare_character(text1, text2)
        elif level == "word":
            return TextComparisonEngine._compare_word(text1, text2)
        elif level == "sentence":
            return TextComparisonEngine._compare_sentence(text1, text2)
        elif level == "paragraph":
            return TextComparisonEngine._compare_paragraph(text1, text2)
        else:
            return TextComparisonEngine._compare_word(text1, text2)

    @staticmethod
    def _compare_character(text1: str, text2: str) -> Dict[str, Any]:
        """Character-level comparison."""
        d = difflib.Differ()
        diff = list(d.compare(text1, text2))
        
        additions = []
        deletions = []
        unchanged = []
        
        for line in diff:
            if line.startswith('+'):
                additions.append(line[2:])
            elif line.startswith('-'):
                deletions.append(line[2:])
            elif line.startswith(' '):
                unchanged.append(line[2:])
        
        similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
        
        return {
            "type": "character",
            "additions": additions,
            "deletions": deletions,
            "unchanged": unchanged,
            "similarity_score": similarity,
            "total_additions": len(additions),
            "total_deletions": len(deletions)
        }

    @staticmethod
    def _compare_word(text1: str, text2: str) -> Dict[str, Any]:
        """Word-level comparison."""
        words1 = text1.split()
        words2 = text2.split()
        
        d = difflib.Differ()
        diff = list(d.compare(words1, words2))
        
        additions = []
        deletions = []
        modifications = []
        unchanged = []
        
        i, j = 0, 0
        while i < len(words1) or j < len(words2):
            if i < len(words1) and j < len(words2):
                if words1[i] == words2[j]:
                    unchanged.append({"word": words1[i], "position": i})
                else:
                    # Check if it's a modification or pure add/delete
                    if i + 1 < len(words1) and words1[i + 1] == words2[j]:
                        deletions.append({"word": words1[i], "position": i})
                        i += 1
                    elif j + 1 < len(words2) and words1[i] == words2[j + 1]:
                        additions.append({"word": words2[j], "position": j})
                        j += 1
                    else:
                        modifications.append({
                            "original": words1[i] if i < len(words1) else None,
                            "modified": words2[j] if j < len(words2) else None,
                            "original_pos": i,
                            "modified_pos": j
                        })
                        i += 1
                        j += 1
                i += 1
                j += 1
            else:
                if i < len(words1):
                    deletions.append({"word": words1[i], "position": i})
                    i += 1
                if j < len(words2):
                    additions.append({"word": words2[j], "position": j})
                    j += 1
        
        similarity = difflib.SequenceMatcher(None, words1, words2).ratio()
        
        return {
            "type": "word",
            "additions": additions,
            "deletions": deletions,
            "modifications": modifications,
            "unchanged": unchanged,
            "similarity_score": similarity,
            "total_additions": len(additions),
            "total_deletions": len(deletions),
            "total_modifications": len(modifications)
        }

    @staticmethod
    def _compare_sentence(text1: str, text2: str) -> Dict[str, Any]:
        """Sentence-level comparison."""
        # Split into sentences
        import re
        sentences1 = re.split(r'[.!?]+', text1)
        sentences2 = re.split(r'[.!?]+', text2)
        
        sentences1 = [s.strip() for s in sentences1 if s.strip()]
        sentences2 = [s.strip() for s in sentences2 if s.strip()]
        
        d = difflib.Differ()
        diff = list(d.compare(sentences1, sentences2))
        
        additions = []
        deletions = []
        modifications = []
        unchanged = []
        
        for line in diff:
            content = line[2:].strip()
            if line.startswith('+'):
                additions.append(content)
            elif line.startswith('-'):
                deletions.append(content)
            elif line.startswith(' '):
                unchanged.append(content)
        
        similarity = difflib.SequenceMatcher(None, sentences1, sentences2).ratio()
        
        return {
            "type": "sentence",
            "additions": additions,
            "deletions": deletions,
            "modifications": modifications,
            "unchanged": unchanged,
            "similarity_score": similarity,
            "total_additions": len(additions),
            "total_deletions": len(deletions)
        }

    @staticmethod
    def _compare_paragraph(text1: str, text2: str) -> Dict[str, Any]:
        """Paragraph-level comparison."""
        paras1 = [p.strip() for p in text1.split('\n\n') if p.strip()]
        paras2 = [p.strip() for p in text2.split('\n\n') if p.strip()]
        
        d = difflib.Differ()
        diff = list(d.compare(paras1, paras2))
        
        additions = []
        deletions = []
        unchanged = []
        
        for line in diff:
            content = line[2:].strip()
            if line.startswith('+'):
                additions.append(content)
            elif line.startswith('-'):
                deletions.append(content)
            elif line.startswith(' '):
                unchanged.append(content)
        
        similarity = difflib.SequenceMatcher(None, paras1, paras2).ratio()
        
        return {
            "type": "paragraph",
            "additions": additions,
            "deletions": deletions,
            "unchanged": unchanged,
            "similarity_score": similarity,
            "total_additions": len(additions),
            "total_deletions": len(deletions)
        }