package com.zombie.victim;

import org.springframework.web.bind.annotation.*;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class UserController {

    private static Map<Integer, User> users = new HashMap<>();
    static {
        users.put(1, new User(1, "Attacker", 100.0, "USER"));
        users.put(2, new User(2, "Rich Victim", 50000.0, "USER"));
    }

    // BOLA Vulnerability
    @GetMapping("/user/{id}")
    public User getUserProfile(@PathVariable int id) {
        return users.get(id);
    }

    // Zombie API Vulnerability
    @PostMapping("/v1/transfer")
    public String transferOld(@RequestBody Map<String, Object> payload) {
        return "Transfer Successful (via V1 Zombie Endpoint)";
    }
}