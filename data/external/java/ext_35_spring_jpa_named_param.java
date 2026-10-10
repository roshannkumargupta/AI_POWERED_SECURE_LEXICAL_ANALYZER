package com.app.dao;

import javax.persistence.EntityManager;

public class SafeItemRepository {
    public Object searchItem(EntityManager em, String keyword) {
        return em.createQuery("SELECT i FROM Item i WHERE i.title = :kw")
                 .setParameter("kw", keyword)
                 .getResultList();
    }
}
