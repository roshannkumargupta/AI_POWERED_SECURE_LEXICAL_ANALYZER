function UserCard({ bio }) {
    return <div dangerouslySetInnerHTML={{ __html: bio }} />;
}
