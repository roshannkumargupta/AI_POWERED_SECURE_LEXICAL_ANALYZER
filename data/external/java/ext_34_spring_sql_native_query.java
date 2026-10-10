package com.app.dao;

import javax.persistence.EntityManager;

public class ItemRepository {
    public Object searchItem(EntityManager em, String keyword) {
        return em.createNativeQuery("SELECT * FROM items WHERE title = '" + keyword + "'").getResultList();
    }
}
