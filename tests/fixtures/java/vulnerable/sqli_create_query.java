import javax.persistence.EntityManager;
import javax.servlet.http.HttpServletRequest;

public class JpaRepo {
    public void findUser(HttpServletRequest req, EntityManager em) {
        String role = req.getParameter("role");
        String q = "SELECT u FROM User u WHERE u.role = '" + role + "'";
        em.createQuery(q).getResultList();
    }
}
