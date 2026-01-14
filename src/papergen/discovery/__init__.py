"""Research discovery modules for papergen.

This package provides tools for:
- Survey analysis and research landscape understanding
- Critical paper identification and deep reading
- Brainstorming and novel idea generation
"""

from .survey import SurveyAnalyzer
from .papers import PaperFinder
from .brainstorm import IdeaGenerator

__all__ = ['SurveyAnalyzer', 'PaperFinder', 'IdeaGenerator']
