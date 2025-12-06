package com.zombie.victim;

import org.springframework.web.bind.annotation.*;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class UserController {

    // 1. The Mock Database
    private static Map<Integer, User> users = new HashMap<>();
    static {
        // ID 1 is the Attacker, ID 2 is the Victim
        users.put(1, new User(1, "Attacker", 100.0, "USER"));
        users.put(2, new User(2, "Rich Victim", 50000.0, "USER"));
        users.put(99, new User(99, "Admin", 0.0, "ADMIN"));
    }

    // 2. The BOLA Vulnerability
    // FLAW: We take {id} from URL and return that user WITHOUT checking who is logged in.
    @GetMapping("/user/{id}")
    public User getUserProfile(@PathVariable int id) {
        return users.get(id);
    }

    // 3. The Zombie API (V1 - Deprecated)
    // FLAW: This endpoint should have been deleted. It has no security checks.
    @PostMapping("/v1/transfer")
    public String transferOld(@RequestBody Map<String, Object> payload) {
        return "Transfer Successful (via V1 Zombie Endpoint) - 💸 Money Sent!";
    }

    // 4. The Secure API (V2 - Current)
    // This is what valid apps should use.
    @PostMapping("/v2/transfer")
    public String transferNew(@RequestBody Map<String, Object> payload) {
        return "Transfer Processed Securely (V2)";
    }
}