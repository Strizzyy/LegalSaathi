import React from 'react';

/**
 * Simple markdown renderer for legal document summaries
 * Converts markdown-style formatting to JSX elements
 */

interface MarkdownRendererProps {
  text: string;
  className?: string;
}

export function MarkdownRenderer({ text, className = '' }: MarkdownRendererProps) {
  if (!text) return null;

  // Process the text to convert markdown to JSX
  const processText = (input: string): React.ReactNode[] => {
    const elements: React.ReactNode[] = [];
    let elementKey = 0;

    // Split by paragraphs first
    const paragraphs = input.split('\n\n').filter(p => p.trim());

    paragraphs.forEach((paragraph) => {
      const trimmedParagraph = paragraph.trim();
      
      // Skip empty paragraphs
      if (!trimmedParagraph) return;

      // Check if it's a header (starts with **)
      if (trimmedParagraph.startsWith('**') && trimmedParagraph.includes('**')) {
        const headerMatch = trimmedParagraph.match(/^\*\*([^*]+)\*\*/);
        if (headerMatch) {
          const headerText = headerMatch[1];
          const remainingText = trimmedParagraph.substring(headerMatch[0].length).trim();
          
          elements.push(
            <div key={`header-${elementKey++}`} className="mb-4">
              <h3 className="text-lg font-bold text-white mb-2 flex items-center">
                <span className="w-2 h-2 bg-cyan-400 rounded-full mr-3"></span>
                {headerText}
              </h3>
              {remainingText && (
                <div className="ml-5 text-slate-200 leading-relaxed">
                  {processInlineFormatting(remainingText)}
                </div>
              )}
            </div>
          );
          return;
        }
      }

      // Regular paragraph
      elements.push(
        <div key={`paragraph-${elementKey++}`} className="mb-4 text-slate-200 leading-relaxed">
          {processInlineFormatting(trimmedParagraph)}
        </div>
      );
    });

    return elements;
  };

  // Process inline formatting (bold, emphasis, etc.)
  const processInlineFormatting = (text: string): React.ReactNode[] => {
    const elements: React.ReactNode[] = [];
    let currentIndex = 0;
    let elementKey = 0;

    // Process bold text (**text**)
    const boldRegex = /\*\*([^*]+)\*\*/g;
    let match;

    while ((match = boldRegex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > currentIndex) {
        const beforeText = text.substring(currentIndex, match.index);
        elements.push(
          <span key={`text-${elementKey++}`}>
            {processOtherFormatting(beforeText)}
          </span>
        );
      }

      // Add the bold text
      elements.push(
        <strong key={`bold-${elementKey++}`} className="font-bold text-white">
          {match[1]}
        </strong>
      );

      currentIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (currentIndex < text.length) {
      const remainingText = text.substring(currentIndex);
      elements.push(
        <span key={`text-${elementKey++}`}>
          {processOtherFormatting(remainingText)}
        </span>
      );
    }

    return elements.length > 0 ? elements : [text];
  };

  // Process other formatting (bullets, numbers, etc.)
  const processOtherFormatting = (text: string): React.ReactNode => {
    // Convert bullet points (- item or • item)
    if (text.includes('\n- ') || text.includes('\n• ')) {
      const lines = text.split('\n');
      const processedLines: React.ReactNode[] = [];
      let inList = false;
      let listItems: React.ReactNode[] = [];
      let elementKey = 0;

      lines.forEach((line) => {
        const trimmedLine = line.trim();
        
        if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('• ')) {
          if (!inList) {
            inList = true;
            listItems = [];
          }
          
          const itemText = trimmedLine.substring(2).trim();
          listItems.push(
            <li key={`item-${elementKey++}`} className="flex items-start space-x-2 mb-2">
              <span className="w-2 h-2 bg-cyan-400 rounded-full mt-2 flex-shrink-0"></span>
              <span>{itemText}</span>
            </li>
          );
        } else {
          if (inList && listItems.length > 0) {
            processedLines.push(
              <ul key={`list-${elementKey++}`} className="space-y-1 my-3">
                {listItems}
              </ul>
            );
            listItems = [];
            inList = false;
          }
          
          if (trimmedLine) {
            processedLines.push(
              <div key={`line-${elementKey++}`} className="mb-2">
                {trimmedLine}
              </div>
            );
          }
        }
      });

      // Handle remaining list items
      if (inList && listItems.length > 0) {
        processedLines.push(
          <ul key={`list-${elementKey++}`} className="space-y-1 my-3">
            {listItems}
          </ul>
        );
      }

      return <div>{processedLines}</div>;
    }

    // Convert numbered lists (1. item, 2. item)
    if (text.match(/\n\d+\.\s/)) {
      const lines = text.split('\n');
      const processedLines: React.ReactNode[] = [];
      let inList = false;
      let listItems: React.ReactNode[] = [];
      let elementKey = 0;

      lines.forEach((line) => {
        const trimmedLine = line.trim();
        const numberMatch = trimmedLine.match(/^(\d+)\.\s(.+)/);
        
        if (numberMatch) {
          if (!inList) {
            inList = true;
            listItems = [];
          }
          
          const number = numberMatch[1];
          const itemText = numberMatch[2];
          listItems.push(
            <li key={`numbered-${elementKey++}`} className="flex items-start space-x-3 mb-2">
              <span className="w-6 h-6 bg-cyan-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-cyan-400 text-xs font-bold">{number}</span>
              </span>
              <span>{itemText}</span>
            </li>
          );
        } else {
          if (inList && listItems.length > 0) {
            processedLines.push(
              <ol key={`numbered-list-${elementKey++}`} className="space-y-1 my-3">
                {listItems}
              </ol>
            );
            listItems = [];
            inList = false;
          }
          
          if (trimmedLine) {
            processedLines.push(
              <div key={`line-${elementKey++}`} className="mb-2">
                {trimmedLine}
              </div>
            );
          }
        }
      });

      // Handle remaining list items
      if (inList && listItems.length > 0) {
        processedLines.push(
          <ol key={`numbered-list-${elementKey++}`} className="space-y-1 my-3">
            {listItems}
          </ol>
        );
      }

      return <div>{processedLines}</div>;
    }

    return text;
  };

  return (
    <div className={`markdown-content ${className}`}>
      {processText(text)}
    </div>
  );
}

// Simple utility for inline text processing
export function processInlineText(text: string): string {
  if (!text) return '';
  
  // Remove markdown formatting for simple text display
  return text
    .replace(/\*\*([^*]+)\*\*/g, '$1') // Remove bold markers
    .replace(/\*([^*]+)\*/g, '$1')     // Remove italic markers
    .replace(/`([^`]+)`/g, '$1')       // Remove code markers
    .trim();
}

// Utility to check if text contains markdown
export function hasMarkdownFormatting(text: string): boolean {
  if (!text) return false;
  
  return /\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\n[-•]\s|\n\d+\.\s/.test(text);
}