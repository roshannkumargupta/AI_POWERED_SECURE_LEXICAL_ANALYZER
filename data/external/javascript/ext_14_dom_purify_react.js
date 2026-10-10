import DOMPurify from 'dompurify';
function SafeProfileBio({ rawBio }) {
    const clean = DOMPurify.sanitize(rawBio);
    return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}
