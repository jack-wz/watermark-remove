import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw'; // To allow HTML in Markdown (use with trusted content)
// import rehypeSanitize from 'rehype-sanitize'; // Or use this for untrusted content for security

// Basic styling for the Markdown content.
// You can expand this or use a CSS file.
const markdownStyles: React.CSSProperties = {
  lineHeight: '1.6',
  // Add more styles as needed, e.g., for headings, lists, code blocks
};

interface MarkdownViewerProps {
  markdownContent: string;
}

const MarkdownViewer: React.FC<MarkdownViewerProps> = ({ markdownContent }) => {
  if (!markdownContent) {
    return <p>No content to display.</p>;
  }

  return (
    <div style={markdownStyles}>
      <ReactMarkdown
        rehypePlugins={[rehypeRaw]} // Add rehypeRaw to process HTML. For untrusted content, use rehypeSanitize.
        // Example of customizing renderers if needed:
        // components={{
        //   h1: ({node, ...props}) => <h1 style={{color: 'blue'}} {...props} />,
        //   p: ({node, ...props}) => <p style={{fontSize: '16px'}} {...props} />,
        // }}
      >
        {markdownContent}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownViewer;
