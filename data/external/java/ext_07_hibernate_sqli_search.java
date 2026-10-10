package com.app.dao;

import javax.persistence.EntityManager;

public class UserDao {
    public Object findByUsername(EntityManager em, String username) {
        String hql = "FROM User WHERE username = '" + username + "'";
        return em.createQuery(hql).getSingleResult();
    }
}
