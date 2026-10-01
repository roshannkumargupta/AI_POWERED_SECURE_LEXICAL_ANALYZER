function UserCard({ bio }) {
    return <div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(bio) }} />;
}
