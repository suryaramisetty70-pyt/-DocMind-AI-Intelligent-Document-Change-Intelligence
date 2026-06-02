"""
DocMind AI - Document Comparison Engine
Multi-level difference detection for documents
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
from difflib import SequenceMatcher, unified_diff, context_diff
import re
from collections import defaultdict


class ChangeType(Enum):
    """Types of document changes"""
    CHARACTER = "character"
    WORD = "word"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    STRUCTURE = "structure"
    INSERTION = "insertion"
    DELETION = "deletion"
    MODIFICATION = "modification"
    MOVEMENT = "movement"
    FORMATTING = "formatting"
    TABLE = "table"


class ChangeSeverity(Enum):
    """Severity levels for changes"""
    MINOR = "minor"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    CRITICAL = "critical"


class ChangeCategory(Enum):
    """Categories of changes"""
    CONTENT = "content"
    STRUCTURE = "structure"
    FORMATTING = "formatting"
    DATA = "data"
    COMPLIANCE = "compliance"


@dataclass
class ChangeLocation:
    """Location of a change in document"""
    page: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    section: Optional[str] = None
    element_id: Optional[str] = None


@dataclass
class Change:
    """Represents a single change between documents"""
    change_type: ChangeType
    location: ChangeLocation
    original_content: str
    modified_content: str
    similarity_score: float = 0.0
    semantic_significance: float = 0.0
    severity: ChangeSeverity = ChangeSeverity.MINOR
    category: ChangeCategory = ChangeCategory.CONTENT
    business_impact: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_summary(self) -> str:
        """Get human-readable change summary"""
        if self.change_type == ChangeType.INSERTION:
            return f"Added: {self.modified_content[:50]}..."
        elif self.change_type == ChangeType.DELETION:
            return f"Removed: {self.original_content[:50]}..."
        elif self.change_type == ChangeType.MODIFICATION:
            return f"Changed from '{self.original_content[:30]}...' to '{self.modified_content[:30]}...'"
        elif self.change_type == ChangeType.MOVEMENT:
            return f"Moved section from {self.metadata.get('from_location')} to {self.metadata.get('to_location')}"
        return f"{self.change_type.value}: {self.original_content[:30]}..."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "change_type": self.change_type.value,
            "location": {
                "page": self.location.page,
                "line_start": self.location.line_start,
                "line_end": self.location.line_end,
                "section": self.location.section
            },
            "original_content": self.original_content,
            "modified_content": self.modified_content,
            "similarity_score": self.similarity_score,
            "semantic_significance": self.semantic_significance,
            "severity": self.severity.value,
            "category": self.category.value,
            "business_impact": self.business_impact,
            "metadata": self.metadata
        }


@dataclass
class ComparisonResult:
    """Complete comparison result between two documents"""
    original_text: str
    modified_text: str
    changes: List[Change]
    statistics: Dict[str, Any]
    overall_similarity: float
    semantic_similarity: float = 0.0
    structural_similarity: float = 0.0
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_summary(self) -> str:
        """Get comparison summary"""
        return f"""
Document Comparison Summary:
- Total Changes: {len(self.changes)}
- Similarity: {self.overall_similarity:.1%}
- Semantic Similarity: {self.semantic_similarity:.1%}
- Structural Similarity: {self.structural_similarity:.1%}

By Type:
{self._count_by_type()}

By Severity:
{self._count_by_severity()}
"""

    def _count_by_type(self) -> str:
        counts = defaultdict(int)
        for change in self.changes:
            counts[change.change_type.value] += 1
        return "\n".join(f"  - {k}: {v}" for k, v in counts.items())
    
    def _count_by_severity(self) -> str:
        counts = defaultdict(int)
        for change in self.changes:
            counts[change.severity.value] += 1
        return "\n".join(f"  - {k}: {v}" for k, v in counts.items())


class CharacterLevelDiff:
    """Character-level difference detection"""
    
    def compare(self, original: str, modified: str) -> List[Change]:
        """Compare two texts at character level"""
        changes = []
        
        matcher = SequenceMatcher(None, original, modified)
        opcodes = matcher.get_opcodes()
        
        line_num = 1
        char_pos = 0
        
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'replace':
                changes.append(Change(
                    change_type=ChangeType.CHARACTER,
                    location=ChangeLocation(line_start=line_num, line_end=line_num),
                    original_content=original[i1:i2],
                    modified_content=modified[j1:j2],
                    similarity_score=0.0,
                    severity=ChangeSeverity.MINOR
                ))
            elif tag == 'delete':
                changes.append(Change(
                    change_type=ChangeType.DELETION,
                    location=ChangeLocation(line_start=line_num, line_end=line_num),
                    original_content=original[i1:i2],
                    modified_content="",
                    similarity_score=0.0,
                    severity=ChangeSeverity.MINOR
                ))
            elif tag == 'insert':
                changes.append(Change(
                    change_type=ChangeType.INSERTION,
                    location=ChangeLocation(line_start=line_num, line_end=line_num),
                    original_content="",
                    modified_content=modified[j1:j2],
                    similarity_score=0.0,
                    severity=ChangeSeverity.MINOR
                ))
        
        return changes


class WordLevelDiff:
    """Word-level difference detection"""
    
    def compare(self, original: str, modified: str) -> List[Change]:
        """Compare two texts at word level"""
        changes = []
        
        original_words = original.split()
        modified_words = modified.split()
        
        matcher = SequenceMatcher(None, original_words, modified_words)
        opcodes = matcher.get_opcodes()
        
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'replace':
                original_text = ' '.join(original_words[i1:i2])
                modified_text = ' '.join(modified_words[j1:j2])
                
                similarity = SequenceMatcher(None, original_text, modified_text).ratio()
                
                changes.append(Change(
                    change_type=ChangeType.WORD,
                    location=ChangeLocation(line_start=i1, line_end=i2),
                    original_content=original_text,
                    modified_content=modified_text,
                    similarity_score=similarity,
                    severity=ChangeSeverity.MODERATE if similarity < 0.5 else ChangeSeverity.MINOR
                ))
            elif tag == 'delete':
                changes.append(Change(
                    change_type=ChangeType.DELETION,
                    location=ChangeLocation(line_start=i1, line_end=i2),
                    original_content=' '.join(original_words[i1:i2]),
                    modified_content="",
                    similarity_score=0.0,
                    severity=ChangeSeverity.MODERATE
                ))
            elif tag == 'insert':
                changes.append(Change(
                    change_type=ChangeType.INSERTION,
                    location=ChangeLocation(line_start=j1, line_end=j2),
                    original_content="",
                    modified_content=' '.join(modified_words[j1:j2]),
                    similarity_score=0.0,
                    severity=ChangeSeverity.MODERATE
                ))
        
        return changes


class SentenceLevelDiff:
    """Sentence-level difference detection"""
    
    def __init__(self):
        self.sentence_splitter = re.compile(r'(?<=[.!?])\s+')
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = self.sentence_splitter.split(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def compare(self, original: str, modified: str) -> List[Change]:
        """Compare two texts at sentence level"""
        changes = []
        
        original_sentences = self._split_sentences(original)
        modified_sentences = self._split_sentences(modified)
        
        matcher = SequenceMatcher(None, original_sentences, modified_sentences)
        opcodes = matcher.get_opcodes()
        
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'replace':
                changes.append(Change(
                    change_type=ChangeType.SENTENCE,
                    location=ChangeLocation(line_start=i1, line_end=i2),
                    original_content=' '.join(original_sentences[i1:i2]),
                    modified_content=' '.join(modified_sentences[j1:j2]),
                    similarity_score=matcher.ratio(),
                    severity=ChangeSeverity.MODERATE
                ))
            elif tag == 'delete':
                changes.append(Change(
                    change_type=ChangeType.DELETION,
                    location=ChangeLocation(line_start=i1, line_end=i2),
                    original_content=' '.join(original_sentences[i1:i2]),
                    modified_content="",
                    similarity_score=0.0,
                    severity=ChangeSeverity.SIGNIFICANT
                ))
            elif tag == 'insert':
                changes.append(Change(
                    change_type=ChangeType.INSERTION,
                    location=ChangeLocation(line_start=j1, line_end=j2),
                    original_content="",
                    modified_content=' '.join(modified_sentences[j1:j2]),
                    similarity_score=0.0,
                    severity=ChangeSeverity.SIGNIFICANT
                ))
        
        return changes


class ParagraphLevelDiff:
    """Paragraph-level difference detection"""
    
    def _split_paragraphs(self, text: str) -> List[Tuple[str, int]]:
        """Split text into paragraphs with line numbers"""
        paragraphs = []
        lines = text.split('\n')
        current_para = []
        current_line = 1
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_para:
                    paragraphs.append(('\n'.join(current_para), current_line))
                    current_para = []
                    current_line += 1
            else:
                if not current_para:
                    current_line = lines.index(line) + 1
                current_para.append(line)
        
        if current_para:
            paragraphs.append(('\n'.join(current_para), current_line - len(current_para) + 1))
        
        return paragraphs
    
    def compare(self, original: str, modified: str) -> List[Change]:
        """Compare two texts at paragraph level"""
        changes = []
        
        original_paragraphs = self._split_paragraphs(original)
        modified_paragraphs = self._split_paragraphs(modified)
        
        orig_texts = [p[0] for p in original_paragraphs]
        mod_texts = [p[0] for p in modified_paragraphs]
        orig_lines = [p[1] for p in original_paragraphs]
        mod_lines = [p[1] for p in modified_paragraphs]
        
        matcher = SequenceMatcher(None, orig_texts, mod_texts)
        opcodes = matcher.get_opcodes()
        
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'replace':
                orig_content = '\n\n'.join(orig_texts[i1:i2])
                mod_content = '\n\n'.join(mod_texts[j1:j2])
                
                changes.append(Change(
                    change_type=ChangeType.PARAGRAPH,
                    location=ChangeLocation(
                        line_start=orig_lines[i1] if i1 < len(orig_lines) else 0,
                        line_end=orig_lines[i2-1] if i2 > i1 and i2-1 < len(orig_lines) else 0
                    ),
                    original_content=orig_content,
                    modified_content=mod_content,
                    similarity_score=matcher.ratio(),
                    severity=ChangeSeverity.SIGNIFICANT,
                    category=ChangeCategory.CONTENT
                ))
            elif tag == 'delete':
                changes.append(Change(
                    change_type=ChangeType.DELETION,
                    location=ChangeLocation(
                        line_start=orig_lines[i1] if i1 < len(orig_lines) else 0,
                        line_end=orig_lines[i2-1] if i2 > i1 and i2-1 < len(orig_lines) else 0
                    ),
                    original_content='\n\n'.join(orig_texts[i1:i2]),
                    modified_content="",
                    similarity_score=0.0,
                    severity=ChangeSeverity.CRITICAL,
                    category=ChangeCategory.CONTENT
                ))
            elif tag == 'insert':
                changes.append(Change(
                    change_type=ChangeType.INSERTION,
                    location=ChangeLocation(
                        line_start=mod_lines[j1] if j1 < len(mod_lines) else 0,
                        line_end=mod_lines[j2-1] if j2 > j1 and j2-1 < len(mod_lines) else 0
                    ),
                    original_content="",
                    modified_content='\n\n'.join(mod_texts[j1:j2]),
                    similarity_score=0.0,
                    severity=ChangeSeverity.SIGNIFICANT,
                    category=ChangeCategory.CONTENT
                ))
        
        return changes


class StructuralDiff:
    """Structural difference detection for document sections"""
    
    def compare(self, original_structure: Dict[str, Any], modified_structure: Dict[str, Any]) -> List[Change]:
        """Compare document structures"""
        changes = []
        
        original_sections = original_structure.get("sections", [])
        modified_sections = modified_structure.get("sections", [])
        
        # Detect added/removed sections
        orig_titles = set(s.get("title", "") for s in original_sections)
        mod_titles = set(s.get("title", "") for s in modified_sections)
        
        added_sections = mod_titles - orig_titles
        removed_sections = orig_titles - mod_titles
        
        for section in original_sections:
            if section.get("title") in removed_sections:
                changes.append(Change(
                    change_type=ChangeType.STRUCTURE,
                    location=ChangeLocation(section=section.get("title")),
                    original_content=f"Section: {section.get('title')}",
                    modified_content="",
                    severity=ChangeSeverity.CRITICAL,
                    category=ChangeCategory.STRUCTURE,
                    metadata={"section_level": section.get("level")}
                ))
        
        for section in modified_sections:
            if section.get("title") in added_sections:
                changes.append(Change(
                    change_type=ChangeType.STRUCTURE,
                    location=ChangeLocation(section=section.get("title")),
                    original_content="",
                    modified_content=f"Section: {section.get('title')}",
                    severity=ChangeSeverity.SIGNIFICANT,
                    category=ChangeCategory.STRUCTURE,
                    metadata={"section_level": section.get("level")}
                ))
        
        # Detect section reordering
        orig_order = [s.get("title") for s in original_sections]
        mod_order = [s.get("title") for s in modified_sections]
        
        common_sections = [s for s in mod_order if s in orig_order]
        for i, title in enumerate(common_sections):
            if i < len(orig_order) and orig_order[i] != title:
                changes.append(Change(
                    change_type=ChangeType.MOVEMENT,
                    location=ChangeLocation(section=title),
                    original_content=f"Section: {title}",
                    modified_content=f"Section: {title}",
                    severity=ChangeSeverity.MODERATE,
                    category=ChangeCategory.STRUCTURE,
                    metadata={
                        "from_position": orig_order.index(title) + 1,
                        "to_position": i + 1
                    }
                ))
        
        return changes


class TableDiff:
    """Table-level difference detection"""
    
    def compare(self, original_tables: List[Dict], modified_tables: List[Dict]) -> List[Change]:
        """Compare tables between documents"""
        changes = []
        
        for idx, (orig_table, mod_table) in enumerate(zip(original_tables, modified_tables)):
            orig_data = orig_table.get("data", [])
            mod_data = mod_table.get("data", [])
            
            if orig_data != mod_data:
                # Compare row by row
                matcher = SequenceMatcher(None, orig_data, mod_data)
                opcodes = matcher.get_opcodes()
                
                for tag, i1, i2, j1, j2 in opcodes:
                    if tag == 'replace':
                        changes.append(Change(
                            change_type=ChangeType.TABLE,
                            location=ChangeLocation(section=f"Table {idx + 1}"),
                            original_content=str(orig_data[i1:i2]),
                            modified_content=str(mod_data[j1:j2]),
                            similarity_score=matcher.ratio(),
                            severity=ChangeSeverity.SIGNIFICANT,
                            category=ChangeCategory.DATA
                        ))
                    elif tag == 'delete':
                        changes.append(Change(
                            change_type=ChangeType.TABLE,
                            location=ChangeLocation(section=f"Table {idx + 1}"),
                            original_content=str(orig_data[i1:i2]),
                            modified_content="",
                            similarity_score=0.0,
                            severity=ChangeSeverity.SIGNIFICANT,
                            category=ChangeCategory.DATA
                        ))
                    elif tag == 'insert':
                        changes.append(Change(
                            change_type=ChangeType.TABLE,
                            location=ChangeLocation(section=f"Table {idx + 1}"),
                            original_content="",
                            modified_content=str(mod_data[j1:j2]),
                            similarity_score=0.0,
                            severity=ChangeSeverity.SIGNIFICANT,
                            category=ChangeCategory.DATA
                        ))
        
        # Check for added/removed tables
        if len(modified_tables) > len(original_tables):
            for idx in range(len(original_tables), len(modified_tables)):
                changes.append(Change(
                    change_type=ChangeType.TABLE,
                    location=ChangeLocation(section=f"Table {idx + 1}"),
                    original_content="",
                    modified_content=f"New table with {modified_tables[idx].get('rows', 0)} rows",
                    severity=ChangeSeverity.MODERATE,
                    category=ChangeCategory.DATA
                ))
        elif len(original_tables) > len(modified_tables):
            for idx in range(len(modified_tables), len(original_tables)):
                changes.append(Change(
                    change_type=ChangeType.TABLE,
                    location=ChangeLocation(section=f"Table {idx + 1}"),
                    original_content=f"Removed table with {original_tables[idx].get('rows', 0)} rows",
                    modified_content="",
                    severity=ChangeSeverity.SIGNIFICANT,
                    category=ChangeCategory.DATA
                ))
        
        return changes


class ChangeAggregator:
    """Aggregate and deduplicate changes from multiple comparison levels"""
    
    def aggregate(self, changes: List[Change]) -> List[Change]:
        """Aggregate similar changes"""
        # Group changes by location and type
        change_groups = defaultdict(list)
        
        for change in changes:
            key = (
                change.change_type,
                change.location.page,
                change.location.section,
                hash(change.original_content + change.modified_content) % 1000
            )
            change_groups[key].append(change)
        
        # Merge groups
        aggregated = []
        for key, group in change_groups.items():
            if len(group) == 1:
                aggregated.append(group[0])
            else:
                # Merge similar changes
                merged = self._merge_changes(group)
                aggregated.append(merged)
        
        return aggregated
    
    def _merge_changes(self, changes: List[Change]) -> Change:
        """Merge multiple similar changes into one"""
        if not changes:
            return None
        
        first = changes[0]
        
        return Change(
            change_type=first.change_type,
            location=first.location,
            original_content=' '.join(c.original_content for c in changes if c.original_content),
            modified_content=' '.join(c.modified_content for c in changes if c.modified_content),
            similarity_score=sum(c.similarity_score for c in changes) / len(changes),
            semantic_significance=max(c.semantic_significance for c in changes),
            severity=max((c.severity for c in changes), key=lambda x: x.value),
            category=first.category,
            metadata={"merged_count": len(changes), "original_changes": [c.to_dict() for c in changes]}
        )


class ComparisonEngine:
    """Main document comparison engine"""
    
    def __init__(self):
        self.character_diff = CharacterLevelDiff()
        self.word_diff = WordLevelDiff()
        self.sentence_diff = SentenceLevelDiff()
        self.paragraph_diff = ParagraphLevelDiff()
        self.structural_diff = StructuralDiff()
        self.table_diff = TableDiff()
        self.aggregator = ChangeAggregator()
    
    def compare(self, original: str, modified: str, level: str = "all") -> ComparisonResult:
        """Compare two documents at specified level(s)"""
        import time
        start_time = time.time()
        
        all_changes = []
        
        if level in ["all", "character"]:
            all_changes.extend(self.character_diff.compare(original, modified))
        
        if level in ["all", "word"]:
            all_changes.extend(self.word_diff.compare(original, modified))
        
        if level in ["all", "sentence"]:
            all_changes.extend(self.sentence_diff.compare(original, modified))
        
        if level in ["all", "paragraph"]:
            all_changes.extend(self.paragraph_diff.compare(original, modified))
        
        # Aggregate changes
        aggregated_changes = self.aggregator.aggregate(all_changes)
        
        # Calculate statistics
        statistics = self._calculate_statistics(original, modified, aggregated_changes)
        
        # Calculate overall similarity
        overall_similarity = self._calculate_similarity(original, modified)
        
        processing_time = time.time() - start_time
        
        return ComparisonResult(
            original_text=original,
            modified_text=modified,
            changes=aggregated_changes,
            statistics=statistics,
            overall_similarity=overall_similarity,
            processing_time=processing_time
        )
    
    def compare_structured(self, original: Dict[str, Any], modified: Dict[str, Any]) -> ComparisonResult:
        """Compare structured documents with layout information"""
        import time
        start_time = time.time()
        
        changes = []
        
        # Compare text
        orig_text = original.get("text_content", "")
        mod_text = modified.get("text_content", "")
        changes.extend(self.paragraph_diff.compare(orig_text, mod_text))
        
        # Compare structure
        changes.extend(self.structural_diff.compare(
            original.get("structure", {}),
            modified.get("structure", {})
        ))
        
        # Compare tables
        changes.extend(self.table_diff.compare(
            original.get("tables", []),
            modified.get("tables", [])
        ))
        
        statistics = self._calculate_statistics(orig_text, mod_text, changes)
        overall_similarity = self._calculate_similarity(orig_text, mod_text)
        
        return ComparisonResult(
            original_text=orig_text,
            modified_text=mod_text,
            changes=self.aggregator.aggregate(changes),
            statistics=statistics,
            overall_similarity=overall_similarity,
            processing_time=time.time() - start_time
        )
    
    def _calculate_statistics(self, original: str, modified: str, changes: List[Change]) -> Dict[str, Any]:
        """Calculate comparison statistics"""
        orig_words = len(original.split())
        mod_words = len(modified.split())
        
        stats = {
            "original_chars": len(original),
            "modified_chars": len(modified),
            "original_words": orig_words,
            "modified_words": mod_words,
            "total_changes": len(changes),
            "insertions": len([c for c in changes if c.change_type == ChangeType.INSERTION]),
            "deletions": len([c for c in changes if c.change_type == ChangeType.DELETION]),
            "modifications": len([c for c in changes if c.change_type == ChangeType.MODIFICATION]),
            "movements": len([c for c in changes if c.change_type == ChangeType.MOVEMENT]),
            "by_severity": {},
            "by_category": {}
        }
        
        # Count by severity
        for severity in ChangeSeverity:
            stats["by_severity"][severity.value] = len([
                c for c in changes if c.severity == severity
            ])
        
        # Count by category
        for category in ChangeCategory:
            stats["by_category"][category.value] = len([
                c for c in changes if c.category == category
            ])
        
        return stats
    
    def _calculate_similarity(self, original: str, modified: str) -> float:
        """Calculate overall similarity score"""
        if not original and not modified:
            return 1.0
        if not original or not modified:
            return 0.0
        
        matcher = SequenceMatcher(None, original, modified)
        return matcher.ratio()
    
    def generate_diff(self, original: str, modified: str, format: str = "unified") -> str:
        """Generate diff in specified format"""
        if format == "unified":
            return '\n'.join(unified_diff(
                original.splitlines(keepends=True),
                modified.splitlines(keepends=True),
                fromfile='original',
                tofile='modified'
            ))
        elif format == "context":
            return '\n'.join(context_diff(
                original.splitlines(keepends=True),
                modified.splitlines(keepends=True),
                fromfile='original',
                tofile='modified'
            ))
        else:
            return ""