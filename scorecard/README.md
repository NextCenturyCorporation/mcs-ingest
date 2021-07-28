
# Scorecard

Given an output json from a run, create a 'scorecard' which evaluates the motion of the 
agent in several dimensions.

The actions that are counted (as of Eval 4 plan):

* Revisiting parts of the room that have not changed
* Attempting to open an un-openable object.  
  * We will begin counting from the first attempt
* Repeating a failed action.   
  * We will begin counting from the second attempt, since it cannot be a “failed” action until after the AI has received 
  feedback from the first attempt. If the AI system attempts the same action from a new position, this will not be considered a repeated action. 
* Attempting physically impossible actions.  
  * e.g., trying to pick up a sofa or another similarly large item; trying to interact with the floor or wall
  * Impossible actions will be counted from the first attempt.  
* Target object in the field of view (not occluded) but agent does not move toward it
  * After a certain number of frames, not moving toward a visible target object will be counted
* Looking into the same container repeatedly
  * If the AI system attempts the same action from a new position, this will not be considered a repeated action

Some of these are mathematically vague;  the space that the agent moves in is continous, 
so 'revisit' needs to have a particular distance.  Below, we discuss the way to count them. 

## Revisiting parts of the Room

Algorithm:
* Divide room (10m x 10m) into a grid of X size. 
* Count the number of times that the agent enters grid squares.
* Note:  if agent goes from point A to point B twice, this can result in many overlaps.
  * Perhaps they should count as one.  
  * Possibly solve by only counting the first in a series of revisits.  
  
   






