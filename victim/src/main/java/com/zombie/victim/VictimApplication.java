package com.zombie.victim;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class VictimApplication {

    public static void main(String[] args) {
        SpringApplication.run(VictimApplication.class, args);
        System.out.println("💀 The Victim is Alive on Port 8080...");
    }

}