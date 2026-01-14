"""LaTeX document builder."""

from pathlib import Path
from typing import Dict, List, Optional, Any
import re

from ..document.citation import CitationManager


class LaTeXBuilder:
    """Builds LaTeX documents from sections."""

    def __init__(self, template: str = "ieee"):
        """
        Initialize LaTeX builder.

        Args:
            template: Template name (ieee, acm, springer, custom)
        """
        self.template = template
        self.sections_content: Dict[str, str] = {}
        self.metadata: Dict[str, Any] = {}
        self.citation_manager: Optional[CitationManager] = None

    def build(
        self,
        sections: Dict[str, str],
        metadata: Dict[str, Any],
        citation_manager: CitationManager,
        template_path: Optional[Path] = None
    ) -> str:
        """
        Build complete LaTeX document.

        Args:
            sections: Dictionary of section_id -> content
            metadata: Paper metadata (title, authors, etc.)
            citation_manager: Citation manager instance
            template_path: Optional custom template path

        Returns:
            Complete LaTeX document as string
        """
        self.sections_content = sections
        self.metadata = metadata
        self.citation_manager = citation_manager

        # Load template
        if template_path:
            with open(template_path, 'r') as f:
                template_text = f.read()
        else:
            template_text = self._get_builtin_template()

        # Replace placeholders
        latex_doc = self._fill_template(template_text)

        return latex_doc

    def _get_builtin_template(self) -> str:
        """Get built-in template text."""
        templates = {
            "ieee": self._get_ieee_template,
            "acm": self._get_acm_template,
            "springer": self._get_springer_template,
            "acl": self._get_acl_template,
            "emnlp": self._get_acl_template,  # EMNLP uses ACL style
            "naacl": self._get_acl_template,  # NAACL uses ACL style
            "aaai": self._get_aaai_template,
            "ijcai": self._get_ijcai_template,
            "neurips": self._get_neurips_template,
            "nips": self._get_neurips_template,  # Alias
            "icml": self._get_icml_template,
        }
        template_func = templates.get(self.template.lower(), self._get_basic_template)
        return template_func()

    def _fill_template(self, template: str) -> str:
        """Fill template with content."""
        # Replace metadata
        template = template.replace("{{TITLE}}", self._escape_latex(self.metadata.get('title', 'Untitled')))
        template = template.replace("{{AUTHORS}}", self._format_authors())
        template = template.replace("{{DATE}}", self.metadata.get('date', r'\today'))

        # Replace sections
        for section_id, content in self.sections_content.items():
            placeholder = f"{{{{{section_id.upper()}}}}}"
            formatted_content = self._format_section_content(content)
            template = template.replace(placeholder, formatted_content)

        # Replace bibliography
        template = template.replace("{{BIBLIOGRAPHY}}", self._format_bibliography())

        return template

    def _format_section_content(self, content: str) -> str:
        """Format section content for LaTeX."""
        # Convert markdown to LaTeX-friendly format
        formatted = content

        # Replace citation markers [CITE:key] with \cite{key}
        formatted = re.sub(r'\[CITE:([^\]]+)\]', r'\\cite{\1}', formatted)

        # Convert markdown headers to LaTeX sections
        # # Header -> \section{Header}
        formatted = re.sub(r'^# (.+)$', r'\\section{\1}', formatted, flags=re.MULTILINE)
        # ## Header -> \subsection{Header}
        formatted = re.sub(r'^## (.+)$', r'\\subsection{\1}', formatted, flags=re.MULTILINE)
        # ### Header -> \subsubsection{Header}
        formatted = re.sub(r'^### (.+)$', r'\\subsubsection{\1}', formatted, flags=re.MULTILINE)

        # Convert markdown bold **text** to \textbf{text}
        formatted = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', formatted)

        # Convert markdown italic *text* to \textit{text}
        formatted = re.sub(r'\*(.+?)\*', r'\\textit{\1}', formatted)

        # Convert markdown lists
        # - item -> \item item (within \begin{itemize})
        lines = formatted.split('\n')
        in_list = False
        result_lines = []
        for line in lines:
            if line.strip().startswith('- '):
                if not in_list:
                    result_lines.append('\\begin{itemize}')
                    in_list = True
                item_text = line.strip()[2:]
                result_lines.append(f'  \\item {item_text}')
            elif line.strip().startswith(r'\d+\. '):
                # Numbered list
                if not in_list:
                    result_lines.append('\\begin{enumerate}')
                    in_list = True
                item_text = re.sub(r'^\d+\.\s+', '', line.strip())
                result_lines.append(f'  \\item {item_text}')
            else:
                if in_list:
                    result_lines.append('\\end{itemize}')
                    in_list = False
                result_lines.append(line)

        if in_list:
            result_lines.append('\\end{itemize}')

        formatted = '\n'.join(result_lines)

        return formatted

    def _format_authors(self) -> str:
        """Format authors for LaTeX."""
        authors = self.metadata.get('authors', [])
        if not authors:
            return 'Anonymous'

        if self.template == "ieee":
            # IEEE format: Name1, Name2, and Name3
            if len(authors) == 1:
                return self._escape_latex(authors[0])
            elif len(authors) == 2:
                return f"{self._escape_latex(authors[0])} and {self._escape_latex(authors[1])}"
            else:
                author_list = ', '.join(self._escape_latex(a) for a in authors[:-1])
                return f"{author_list}, and {self._escape_latex(authors[-1])}"
        else:
            # Default format
            return r' \and '.join(self._escape_latex(a) for a in authors)

    def _format_bibliography(self) -> str:
        """Format bibliography."""
        if not self.citation_manager or not self.citation_manager.citations:
            return '% No references'

        # Generate BibTeX entries
        bibtex = self.citation_manager.export_bibtex()

        # For IEEE, return bibliography command
        if self.template == "ieee":
            return bibtex
        else:
            return bibtex

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters."""
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\^{}',
            '\\': r'\textbackslash{}',
        }
        for char, escaped in replacements.items():
            text = text.replace(char, escaped)
        return text

    def _get_ieee_template(self) -> str:
        """Get IEEE template."""
        return r"""\documentclass[conference]{IEEEtran}
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}

\begin{document}

\title{{{TITLE}}}

\author{\IEEEauthorblockN{{{AUTHORS}}}}

\maketitle

\begin{abstract}
{{ABSTRACT}}
\end{abstract}

{{INTRODUCTION}}

{{RELATED_WORK}}

{{METHODS}}

{{METHODOLOGY}}

{{RESULTS}}

{{DISCUSSION}}

{{CONCLUSION}}

\begin{thebibliography}{99}
{{BIBLIOGRAPHY}}
\end{thebibliography}

\end{document}
"""

    def _get_acm_template(self) -> str:
        """Get ACM template."""
        return r"""\documentclass[sigconf]{acmart}

\begin{document}

\title{{{TITLE}}}

\author{{{AUTHORS}}}

\begin{abstract}
{{ABSTRACT}}
\end{abstract}

\maketitle

{{INTRODUCTION}}

{{RELATED_WORK}}

{{METHODS}}

{{METHODOLOGY}}

{{RESULTS}}

{{DISCUSSION}}

{{CONCLUSION}}

\bibliographystyle{ACM-Reference-Format}
\begin{thebibliography}{99}
{{BIBLIOGRAPHY}}
\end{thebibliography}

\end{document}
"""

    def _get_springer_template(self) -> str:
        """Get Springer template."""
        return r"""\documentclass{llncs}
\usepackage{cite}
\usepackage{graphicx}

\begin{document}

\title{{{TITLE}}}

\author{{{AUTHORS}}}

\maketitle

\begin{abstract}
{{ABSTRACT}}
\end{abstract}

{{INTRODUCTION}}

{{RELATED_WORK}}

{{METHODS}}

{{METHODOLOGY}}

{{RESULTS}}

{{DISCUSSION}}

{{CONCLUSION}}

\bibliographystyle{splncs04}
\begin{thebibliography}{99}
{{BIBLIOGRAPHY}}
\end{thebibliography}

\end{document}
"""

    def _get_basic_template(self) -> str:
        """Get basic article template."""
        return r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{cite}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage{hyperref}

\title{{{TITLE}}}
\author{{{AUTHORS}}}
\date{{{DATE}}}

\begin{document}

\maketitle

\begin{abstract}
{{ABSTRACT}}
\end{abstract}

{{INTRODUCTION}}

{{RELATED_WORK}}

{{METHODS}}

{{METHODOLOGY}}

{{RESULTS}}

{{DISCUSSION}}

{{CONCLUSION}}

\bibliographystyle{plain}
\begin{thebibliography}{99}
{{BIBLIOGRAPHY}}
\end{thebibliography}

\end{document}
"""

    def _get_acl_template(self) -> str:
        """Get ACL/EMNLP/NAACL template."""
        return r"""\documentclass[11pt]{article}
\usepackage[hyperref]{acl}
\usepackage{times}
\usepackage{latexsym}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}

\title{{{TITLE}}}
\author{{{AUTHORS}}}

\begin{document}
\maketitle

\begin{abstract}
{{ABSTRACT}}
\end{abstract}

{{INTRODUCTION}}

{{BACKGROUND}}

{{RELATED_WORK}}

{{METHODS}}

{{METHODOLOGY}}

{{RESULTS}}

{{DISCUSSION}}

{{CONCLUSION}}

\bibliography{references}
\bibliographystyle{acl_natbib}

\end{document}
"""

    def _get_aaai_template(self) -> str:
        """Get AAAI template."""
        return r"""\documentclass[letterpaper]{article}
\usepackage{aaai24}
\usepackage{times}
\usepackage{helvet}
\usepackage{courier}
\usepackage[hyphens]{url}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{booktabs}

\title{{{TITLE}}}
\author{{{AUTHORS}}}

\begin{document}
\maketitle

\begin{abstract}
{{ABSTRACT}}
\end{abstract}

{{INTRODUCTION}}

{{BACKGROUND}}

{{RELATED_WORK}}

{{METHODS}}

{{METHODOLOGY}}

{{RESULTS}}

{{DISCUSSION}}

{{CONCLUSION}}

\bibliography{references}

\end{document}
"""

    def _get_ijcai_template(self) -> str:
        """Get IJCAI template."""
        return r"""\documentclass{article}
\pdfpagewidth=8.5in
\pdfpageheight=11in
\usepackage{ijcai24}
\usepackage{times}
\usepackage{soul}
\usepackage{url}
\usepackage[hidelinks]{hyperref}
\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{booktabs}

\title{{{TITLE}}}
\author{{{AUTHORS}}}

\begin{document}
\maketitle

\begin{abstract}
{{ABSTRACT}}
\end{abstract}

{{INTRODUCTION}}

{{BACKGROUND}}

{{RELATED_WORK}}

{{METHODS}}

{{METHODOLOGY}}

{{RESULTS}}

{{DISCUSSION}}

{{CONCLUSION}}

\bibliography{references}

\end{document}
"""

    def _get_neurips_template(self) -> str:
        """Get NeurIPS template."""
        return r"""\documentclass{article}
\usepackage[final]{neurips_2024}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{hyperref}
\usepackage{url}
\usepackage{booktabs}
\usepackage{amsfonts}
\usepackage{amsmath}
\usepackage{nicefrac}
\usepackage{microtype}
\usepackage{graphicx}

\title{{{TITLE}}}
\author{{{AUTHORS}}}

\begin{document}
\maketitle

\begin{abstract}
{{ABSTRACT}}
\end{abstract}

{{INTRODUCTION}}

{{BACKGROUND}}

{{RELATED_WORK}}

{{METHODS}}

{{METHODOLOGY}}

{{RESULTS}}

{{DISCUSSION}}

{{CONCLUSION}}

\bibliography{references}
\bibliographystyle{unsrtnat}

\end{document}
"""

    def _get_icml_template(self) -> str:
        """Get ICML template."""
        return r"""\documentclass{article}
\usepackage{icml2024}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{mathtools}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{url}

\begin{document}

\twocolumn[
\icmltitle{{{TITLE}}}

\begin{icmlauthorlist}
\icmlauthor{{{AUTHORS}}}{}
\end{icmlauthorlist}

\vskip 0.3in
]

\printAffiliationsAndNotice{}

\begin{abstract}
{{ABSTRACT}}
\end{abstract}

{{INTRODUCTION}}

{{BACKGROUND}}

{{RELATED_WORK}}

{{METHODS}}

{{METHODOLOGY}}

{{RESULTS}}

{{DISCUSSION}}

{{CONCLUSION}}

\bibliography{references}
\bibliographystyle{icml2024}

\end{document}
"""
