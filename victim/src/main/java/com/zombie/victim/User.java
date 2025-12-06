package com.zombie.victim;

public class User {
    private int id;
    private String name;
    private double balance;
    private String role;

    public User(int id, String name, double balance, String role) {
        this.id = id;
        this.name = name;
        this.balance = balance;
        this.role = role;
    }

    public int getId() { return id; }
    public String getName() { return name; }
    public double getBalance() { return balance; }
    public String getRole() { return role; }
}