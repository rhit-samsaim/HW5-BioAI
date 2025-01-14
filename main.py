import pygame
import random
import neat

# Initialize pygame
pygame.init()

# Set up display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Traffic Intersection Simulation")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
GRAY = (169, 169, 169)

# Intersection stopping zones
STOP_ZONE_X_E = width // 2 - 100
STOP_ZONE_Y_W = height // 2 - 100
STOP_ZONE_X_W = width // 2 + 100
STOP_ZONE_Y_E = height // 2 + 100

# Track Cars
carsEW = 0
carsWE = 0
carsNS = 0
carsSN = 0
cars_finished = 0


# Car class
class Car:
    def __init__(self, x, y, direction, start_time):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = 6
        self.is_stopped = False
        self.passed_intersection = False
        self.start_time = start_time
        if direction == 'east-west':
            self.cars_at_time = carsEW
        elif direction == 'west-east':
            self.cars_at_time = carsWE
        elif direction == 'north-south':
            self.cars_at_time = carsNS
        elif direction == 'south-north':
            self.cars_at_time = carsSN

    def move(self, traffic_light):
        global carsEW, carsWE, carsNS, carsSN
        # Stop condition for each direction
        if self.direction == 'east-west':
            near_intersection = STOP_ZONE_X_E - (self.cars_at_time * 50) + 50 <= self.x <= STOP_ZONE_X_E + 10
            stop_for_red = traffic_light.state == 'north-south' or traffic_light.color == RED
        elif self.direction == 'north-south':
            near_intersection = STOP_ZONE_Y_W - (self.cars_at_time * 50) + 50 <= self.y <= STOP_ZONE_Y_W + 10
            stop_for_red = traffic_light.state == 'east-west' or traffic_light.color == RED
        elif self.direction == 'south-north':
            near_intersection = STOP_ZONE_Y_E - 50 <= self.y <= STOP_ZONE_Y_E - 40 + (self.cars_at_time * 50) - 50
            stop_for_red = traffic_light.state == 'east-west' or traffic_light.color == RED
        elif self.direction == 'west-east':
            near_intersection = STOP_ZONE_X_W - 50 <= self.x <= STOP_ZONE_X_W - 40 + (self.cars_at_time * 50) - 50
            stop_for_red = traffic_light.state == 'north-south' or traffic_light.color == RED

        # Stop or move logic
        if near_intersection and stop_for_red:
            self.is_stopped = True
        else:
            self.is_stopped = False

        # Move if not stopped
        if not self.is_stopped:
            if self.direction == 'east-west':
                self.x += self.speed
            elif self.direction == 'west-east':
                self.x -= self.speed
            elif self.direction == 'north-south':
                self.y += self.speed
            elif self.direction == 'south-north':
                self.y -= self.speed

    def passedIntersection(self):
        global carsEW, carsWE, carsNS, carsSN
        if self.direction == 'east-west':
            if not self.passed_intersection and self.x > width // 2:
                carsEW -= 1
                self.passed_intersection = True
        elif self.direction == 'west-east':
            if not self.passed_intersection and self.x < width // 2:
                carsWE -= 1
                self.passed_intersection = True
        elif self.direction == 'north-south':
            if not self.passed_intersection and self.y > height // 2:
                carsNS -= 1
                self.passed_intersection = True
        elif self.direction == 'south-north':
            if not self.passed_intersection and self.y < height // 2:
                carsSN -= 1
                self.passed_intersection = True
        return self.passed_intersection

    def draw(self):
        if self.direction in ['east-west', 'west-east']:
            pygame.draw.rect(screen, BLACK, (self.x, self.y, 40, 20))  # Horizontal car
        else:
            pygame.draw.rect(screen, BLACK, (self.x, self.y, 20, 40))  # Vertical car

    def get_final_time(self, current_time):
        return current_time - self.start_time

    def get_start_time(self):
        return self.start_time


# Traffic light class
class TrafficLight:
    def __init__(self):
        self.state = 'east-west'  # 'east-west' or 'north-south'
        self.color = GREEN
        self.buffer_time = 0  # Buffer time for delay after light change

    def change(self):
        global carsEW, carsWE, carsNS, carsSN
        # Switch between directions and apply buffer time
        if self.buffer_time == 0:  # Only change if there's no active buffer
            self.buffer_time = 2000  # 2 second buffer time
            if self.state == 'east-west':
                self.state = 'north-south'
                self.color = GREEN
            else:
                self.state = 'east-west'
                self.color = GREEN  # Ensure green for the switched state

    def update(self):
        # Decrease buffer time and stop cars from moving during this time
        if self.buffer_time > 0:
            self.buffer_time -= 30  # Decrease by 30 milliseconds (based on pygame.time.delay)
        elif self.buffer_time < 0:
            self.buffer_time = 0

    def draw(self):
        # Set light color based on buffer_time
        if self.buffer_time > 0:
            light_color = YELLOW  # Show yellow light when buffer_time is not zero
        else:
            light_color = GREEN if self.state == 'north-south' else RED
        pygame.draw.rect(screen, BLACK, (width // 2 - 25, height // 2 - 25, 50, 50))
        pygame.draw.circle(screen, light_color, (width // 2, height // 2), 20)


# Draw button
def draw_button():
    pygame.draw.rect(screen, (0, 128, 255), (width - 150, height - 50, 120, 30))  # Button
    font = pygame.font.SysFont('Arial', 20)
    text = font.render('Change Light', True, WHITE)
    screen.blit(text, (width - 140, height - 45))


# Game loop
traffic_light = TrafficLight()
cars = []
total_time = 0


def delete_car(car_to_remove, time):
    global total_time, cars_finished
    if car_to_remove.x > 830 or car_to_remove.x < -30 or car_to_remove.y > 630 or car_to_remove.y < -30:
        total_time += car_to_remove.get_final_time(time)
        cars_finished += 1
        cars.remove(car_to_remove)
        return True
    return False


def evaluate_genomes(genomes, config):
    global cars_finished, carsEW, carsWE, carsNS, carsSN, total_time, cars, traffic_light

    # Create neural networks for each genome
    for genome_id, genome in genomes:
        total_time, carsEW, carsWE, carsNS, carsSN = 0, 0, 0, 0, 0
        cars_finished = 0
        last_car_time = pygame.time.get_ticks()
        random_time_interval = 0
        traffic_light = TrafficLight()
        cars = []

        network = neat.nn.FeedForwardNetwork.create(genome, config)

        while cars_finished < 10:  # Continue until 20 cars have passed the intersection
            screen.fill(WHITE)  # Clear the screen for each frame

            pygame.draw.rect(screen, GRAY, (0, height // 2 - 50, width, 100))  # horizontal road
            pygame.draw.rect(screen, GRAY, (width // 2 - 50, 0, 100, height))  # vertical road

            # Get the current state for the network input
            cars_waiting_ew = 0
            cars_waiting_ns = 0
            for car in cars:
                if car.direction == 'east-west' or 'west-east':
                    cars_waiting_ew += car.get_start_time()
                else:  # 'south-north' / 'north-south'
                    cars_waiting_ns += car.get_start_time()

            if traffic_light.state == 'east-west' or traffic_light.state == 'west-east':
                light_state = 1  # green
            else:
                light_state = 0 # red

            # Prepare the input for the neural network
            inputs = [float(cars_waiting_ew), float(cars_waiting_ns), light_state]

            # Get the network decision
            output = network.activate(inputs)
            if output[0] > 0.5 or output[0] < 0.00001: # If the output is greater than 0.5, change the light
                traffic_light.change()

            # Update and draw the traffic light
            traffic_light.update()
            traffic_light.draw()

            current_time = pygame.time.get_ticks()
            if current_time - last_car_time >= random_time_interval:
                random_time_interval = random.randint(800, 800)
                direction = random.choice(['east-west', 'west-east', 'north-south', 'south-north'])
                if direction == 'east-west':
                    carsEW += 1
                    x = 0  # Starting from left
                    y = 315
                elif direction == 'west-east':
                    carsWE += 1
                    x = width  # Starting from right
                    y = 270
                elif direction == 'north-south':
                    carsNS += 1
                    x = 370
                    y = 0  # Starting from top
                else:  # 'south-north'
                    carsSN += 1
                    x = 415
                    y = height  # Starting from bottom

                cars.append(Car(x, y, direction, pygame.time.get_ticks()))
                last_car_time = current_time  # Update the last car generation time

            # Move cars and check if they passed the intersection
            for car in cars:
                if not delete_car(car, pygame.time.get_ticks()):
                    car.passedIntersection()
                    car.move(traffic_light)
                    car.draw()

            # Update the screen and limit FPS using delay
            pygame.display.update()
            pygame.time.delay(30)

        for car in cars:
            cars.remove(car)
        fitness_value = 1 / (total_time / (5000 * 10)) # put in seconds 5000 <- time for car to pass without stopping on average
        genome.fitness = fitness_value


# Set up the NEAT configuration
config_file = "config-feedforward"  # Path to your config file
config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                            neat.DefaultSpeciesSet, neat.DefaultStagnation,
                            config_file)

# Initialize the population
population = neat.Population(config)

# Set the initial fitness of all genomes to 0
for genome_id, genome in population.population.items():
    genome.fitness = 0  # Set fitness to 0 for all genomes

# Add a reporter to show the progress of evolution
population.add_reporter(neat.StdOutReporter(True))
population.add_reporter(neat.StatisticsReporter())

# Run the NEAT algorithm
population.run(evaluate_genomes, 5)  # Run for 5 generations
pygame.quit()


# THIS CODE IS FOR NON-NEAT TO SEE IF IT WORKED WHICH IT DOES

# import pygame
# import random
# import neat
#
# # Initialize pygame
# pygame.init()
#
# # Set up display
# width, height = 800, 600
# screen = pygame.display.set_mode((width, height))
# pygame.display.set_caption("Traffic Intersection Simulation")
#
# # Colors
# WHITE = (255, 255, 255)
# RED = (255, 0, 0)
# GREEN = (0, 255, 0)
# YELLOW = (255, 255, 0)
# BLACK = (0, 0, 0)
# GRAY = (169, 169, 169)
#
# # Intersection stopping zones
# STOP_ZONE_X_E = width // 2 - 100
# STOP_ZONE_Y_W = height // 2 - 100
# STOP_ZONE_X_W = width // 2 + 100
# STOP_ZONE_Y_E = height // 2 + 100
#
# # Track Cars
# carsEW = 0
# carsWE = 0
# carsNS = 0
# carsSN = 0
# cars_finished = 0
#
#
# # Car class
# class Car:
#     def __init__(self, x, y, direction, start_time):
#         self.x = x
#         self.y = y
#         self.direction = direction
#         self.speed = 6
#         self.is_stopped = False
#         self.passed_intersection = False
#         self.start_time = start_time
#         if direction == 'east-west':
#             self.cars_at_time = carsEW
#         elif direction == 'west-east':
#             self.cars_at_time = carsWE
#         elif direction == 'north-south':
#             self.cars_at_time = carsNS
#         elif direction == 'south-north':
#             self.cars_at_time = carsSN
#
#     def move(self, traffic_light):
#         global carsEW, carsWE, carsNS, carsSN
#         # Stop condition for each direction
#         if self.direction == 'east-west':
#             near_intersection = STOP_ZONE_X_E - (self.cars_at_time * 50) + 50 <= self.x <= STOP_ZONE_X_E + 10
#             stop_for_red = traffic_light.state == 'north-south' or traffic_light.color == RED
#         elif self.direction == 'north-south':
#             near_intersection = STOP_ZONE_Y_W - (self.cars_at_time * 50) + 50 <= self.y <= STOP_ZONE_Y_W + 10
#             stop_for_red = traffic_light.state == 'east-west' or traffic_light.color == RED
#         elif self.direction == 'south-north':
#             near_intersection = STOP_ZONE_Y_E - 50 <= self.y <= STOP_ZONE_Y_E - 40 + (self.cars_at_time * 50) - 50
#             stop_for_red = traffic_light.state == 'east-west' or traffic_light.color == RED
#         elif self.direction == 'west-east':
#             near_intersection = STOP_ZONE_X_W - 50 <= self.x <= STOP_ZONE_X_W - 40 + (self.cars_at_time * 50) - 50
#             stop_for_red = traffic_light.state == 'north-south' or traffic_light.color == RED
#
#         # Stop or move logic
#         if near_intersection and stop_for_red:
#             self.is_stopped = True
#         else:
#             self.is_stopped = False
#
#         # Move if not stopped
#         if not self.is_stopped:
#             if self.direction == 'east-west':
#                 self.x += self.speed
#             elif self.direction == 'west-east':
#                 self.x -= self.speed
#             elif self.direction == 'north-south':
#                 self.y += self.speed
#             elif self.direction == 'south-north':
#                 self.y -= self.speed
#
#     def passedIntersection(self):
#         global carsEW, carsWE, carsNS, carsSN
#         if self.direction == 'east-west':
#             if not self.passed_intersection and self.x > width // 2:
#                 carsEW -= 1
#                 self.passed_intersection = True
#         elif self.direction == 'west-east':
#             if not self.passed_intersection and self.x < width // 2:
#                 carsWE -= 1
#                 self.passed_intersection = True
#         elif self.direction == 'north-south':
#             if not self.passed_intersection and self.y > height // 2:
#                 carsNS -= 1
#                 self.passed_intersection = True
#         elif self.direction == 'south-north':
#             if not self.passed_intersection and self.y < height // 2:
#                 carsSN -= 1
#                 self.passed_intersection = True
#
#     def draw(self):
#         if self.direction in ['east-west', 'west-east']:
#             pygame.draw.rect(screen, BLACK, (self.x, self.y, 40, 20))  # Horizontal car
#         else:
#             pygame.draw.rect(screen, BLACK, (self.x, self.y, 20, 40))  # Vertical car
#
#     def get_final_time(self, current_time):
#         return current_time - self.start_time
#
#
# # Traffic light class
# class TrafficLight:
#     def __init__(self):
#         self.state = 'east-west'  # 'east-west' or 'north-south'
#         self.color = GREEN
#         self.buffer_time = 0  # Buffer time for delay after light change
#
#     def change(self):
#         global carsEW, carsWE, carsNS, carsSN
#         # Switch between directions and apply buffer time
#         if self.buffer_time == 0:  # Only change if there's no active buffer
#             self.buffer_time = 2000  # 2 second buffer time
#             if self.state == 'east-west':
#                 self.state = 'north-south'
#                 self.color = GREEN
#             else:
#                 self.state = 'east-west'
#                 self.color = GREEN  # Ensure green for the switched state
#
#     def update(self):
#         # Decrease buffer time and stop cars from moving during this time
#         if self.buffer_time > 0:
#             self.buffer_time -= 30  # Decrease by 30 milliseconds (based on pygame.time.delay)
#         elif self.buffer_time < 0:
#             self.buffer_time = 0
#
#     def draw(self):
#         # Set light color based on buffer_time
#         if self.buffer_time > 0:
#             light_color = YELLOW  # Show yellow light when buffer_time is not zero
#         else:
#             light_color = GREEN if self.state == 'north-south' else RED
#         pygame.draw.rect(screen, BLACK, (width // 2 - 25, height // 2 - 25, 50, 50))
#         pygame.draw.circle(screen, light_color, (width // 2, height // 2), 20)
#
#
# # Draw button
# def draw_button():
#     pygame.draw.rect(screen, (0, 128, 255), (width - 150, height - 50, 120, 30))  # Button
#     font = pygame.font.SysFont('Arial', 20)
#     text = font.render('Change Light', True, WHITE)
#     screen.blit(text, (width - 140, height - 45))
#
#
# # Game loop
# traffic_light = TrafficLight()
# cars = []
# total_time = 0
#
#
# def delete_car(car_to_remove, time):
#     global total_time, cars_finished
#     if car_to_remove.x > 830 or car_to_remove.x < -30 or car_to_remove.y > 630 or car_to_remove.y < -30:
#         total_time += car_to_remove.get_final_time(time)
#         cars_finished += 1
#         cars.remove(car_to_remove)
#         return True
#     return False
# # Timer for generating cars (3-second interval)
# last_car_time = pygame.time.get_ticks()
#
# running = True
#
# while cars_finished < 20 and running:
#     screen.fill(WHITE)
#
#     # Draw the intersection
#     pygame.draw.rect(screen, GRAY, (0, height // 2 - 50, width, 100))  # horizontal road
#     pygame.draw.rect(screen, GRAY, (width // 2 - 50, 0, 100, height))  # vertical road
#     traffic_light.draw()
#
#     # Move and draw cars
#     for car in cars:
#         if not delete_car(car, pygame.time.get_ticks()):
#             car.passedIntersection()
#             car.move(traffic_light)
#             car.draw()
#
#     # Draw the button
#     draw_button()
#
#     # Event handling
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False
#         if event.type == pygame.MOUSEBUTTONDOWN:
#             mouse_x, mouse_y = event.pos
#             # Check if the button is clicked
#             if width - 150 <= mouse_x <= width - 30 and height - 50 <= mouse_y <= height - 20:
#                 # Change the light on button click
#                 traffic_light.change()
#
#     # Update the traffic light buffer time (delay)
#     traffic_light.update()
#
#     # Car generation logic (every 3 seconds)
#     current_time = pygame.time.get_ticks()
#     if current_time - last_car_time >= 1200:  # 1.2 seconds passed
#         # Randomly choose direction and position
#         direction = random.choice(['east-west', 'west-east', 'north-south', 'south-north'])
#
#         if direction == 'east-west':
#             carsEW += 1
#             x = 0  # Starting from left
#             y = 315
#         elif direction == 'west-east':
#             carsWE += 1
#             x = width  # Starting from right
#             y = 270
#         elif direction == 'north-south':
#             carsNS += 1
#             x = 370
#             y = 0  # Starting from top
#         else:  # 'south-north'
#             carsSN += 1
#             x = 415
#             y = height  # Starting from bottom
#
#         cars.append(Car(x, y, direction, pygame.time.get_ticks()))
#         last_car_time = current_time  # Update the last car generation time
#
#     # Update the display
#     pygame.display.update()
#
#     pygame.time.delay(30)
#
# pygame.quit()
