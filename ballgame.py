import cv2
import numpy as np
import random

ball_radius=10
ball_position=[random.randint(ball_radius,500-ball_radius),0]
ball_velocity=[0,random.uniform(3,7)]
while True:
    ball_position[1]+=ball_velocity[1]
    if ball_position[1]>= 500-ball_radius:
        ball_position=[random.randint(ball_radius,500-ball_radius),0]
        ball_velocity=[0,random.uniform(3,7)]  
    game_window = np.zeros((500,500,3),dtype=np.uint8)
    cv2.circle(game_window,(int(ball_position[0]),int(ball_position[1])),ball_radius,(0,0,255),-1)
    cv2.imshow('catch the ball',game_window)
    if cv2.waitKey(1) & 0xFF == ord('s'):
        break
cv2.destroyAllwindows()