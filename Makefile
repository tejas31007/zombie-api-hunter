# Zombie Hunter Command Center

.PHONY: up down build clean logs

# Start the system
up:
	docker-compose up

# Stop the system
down:
	docker-compose down

# Rebuild everything (use this if you change code)
build:
	docker-compose up --build

# View logs
logs:
	docker-compose logs -f

# Clean up (remove stopped containers and networks)
clean:
	docker system prune -f