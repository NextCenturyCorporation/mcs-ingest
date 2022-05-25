
# Scorecard

Given an output json from a run, create a 'scorecard' which evaluates the motion of the
agent in several dimensions.

The actions that are counted (as of Eval 5):

* Revisiting parts of the room that have not changed
* Attempting to open an un-openable object.
  * We will begin counting from the first attempt
* Looking into the same container repeatedly
* Target object in the field of view but agent does not move toward it
  * After a certain number of frames, not moving toward a visible target object will be counted
* Repeating a failed action.
  * We will begin counting from the second attempt, since it cannot be a “failed” action until after the AI has received
  feedback from the first attempt. If the AI system attempts the same action from a new position, this will not be considered a repeated action.
* Actions on ramps, including whether the agent successfully went up, abandonded going up 
  or down, and fell off
* Moving, rotating, torquing interactions with objects
* Determine which side of the platform the agent went to (correct or incorrect)
* Determine which door the agent went to (correct or incorrect)
* Attempting physically impossible actions.  This is not implemented yet.
  * e.g., trying to pick up a sofa or another similarly large item; trying to interact with the floor or wall
  * Impossible actions will be counted from the first attempt.
  
Some of these are mathematically vague;  for example, the space that the agent moves in is continous,
so 'revisit' needs to have a particular distance.  Below, we discuss the way to count them.

# Algorithms

Note that the algorithms depend on parameters, such as grid size.  
These parameters are all in the top of ```scorecard.py``` and the 
reader is urged to review those values.  

#### Revisiting parts of the Room

Algorithm:
* Divide room into a grid of 0.5 m
* Count the number of times that the agent enters a
grid square while facing in the same direction (within 10 degrees) as a
previous time they were in that grid square
* If paths cross while facing in different directions, it does not count as a revist
* If the actor rotates or does not move (PASS), it does not count
  * Note that this means that if the actor spins in a circle and then passes over
    that location in any direction later, it will count as a revist
* Note:  if agent travels from point A to point B twice, this can result in many overlaps.
  * They only count as one.
  * Implement this as only counting the first in a series of revisits.

#### Attempting to Open an UnOpenable object

This counts the number of times that the agent tried to open something
and failed because it was something they were not supposed to be
openning.

Notably, this does _not_ include IS_OPENED_COMPLETELY which is what
is returned if you try to open an already-opened object and OUT_OF_REACH
which is returned when you try to open an openable object but it is
too far away.  Everything else causes the count of unopenable objects to
increase.

#### Looking into the Same Container Repeatedly

If the agent looks in the same container repeatedly, count it (after the
first look).  Algorithm:
* If the agent goes up to a container and OPENs it, that counts as the
first time
* If the agent goes to the open container and looks down
into the container, that counts as a second time
  * Looking down requires tilt >= 30 and the gaze point to be
  within 0.4 of the container
* If the agent closes the container and then re-opens, it still counts
* Moving around / tilting while looking in the container only counts as a
single look.  This is implemented by ignoring the next 10 movements and setting
a flag that they are still looking
* Passing the container without looking into it does not count

Note:   The orientation of the container is not being taken into account.  That is,
if the container was opened but the hinge of the lid was facing the agent so
they could not see into it, then it still counts as the first time.  Going around
the container so that they can actually look into it counts as a second look.
It is recognized that this is a limitation of the algorithm.

#### Target object in the field of view but agent does not move toward it

If the agent can see the target object, it should move toward it.  This is slightly
more complicated than that because there might be objects in the way or the target may not
be very visible (a single pixel on the edge of the field of view).

Algorithm:
  * The target needs to be visible for a number of frames in a row (4) before it counts
  as being sufficiently visible that the agent should have seen it.  A timer is then
  started and the distance to the target is saved
  * After 30 steps, the agent should have had time to go around whatever is in the way
  and moved closer to the target.
  * If it doesn't move towards the target, then we increment by one and reset
  * If it does move towards the target, it needs to continue moving towards
  the target (within the next 30 steps)

The number 30 is to give the agent sufficient time to go around an obstacle. We
ignore turns, passes, tilts, etc and only count MoveAhead, MoveBack, MoveLeft,
and MoveRight.  It takes maybe 15 steps to the side to get past an object
(during which distance will increase), and then some number of steps to make
up for the fact that the agent was moving away while going around the obstacle
(15).  Based on some testing, 30 is about right.


#### Repeated Failed Actions

If the agent repeatedly tries an action and fails, then it should be counted.
For each action type (Open / Close, Pickup, etc), we note when it fails a
first time.  If the same action type is done again with the same failure
type, from the same position/rotation, with the same action parameters, it
counts.

Because of the difficulty in moving, if the agent tries to move and it is
OBSTRUCTED, it is _not_ counted.

Note that this overlaps with some of the other scorecard elements.  For example,
attempting to open an unopenable object will cause it to count in that category.
This one will count if the agent tries to do it twice (or more times).  If the
agent does it twice, then the unopenable object count will be 2 and the
repeated failed actions will 1.

#### Ramp Actions 

Keep track of all the things that could happen on a ramp.  They include:
* Going up the ramp successfully
* Starting to go up the ramp and then going back down
* Going down a ramp successfully
* Starting to go down a ramp, but then going back up
* Falling off a ramp

The calculations for ramp actions are complicated by the fact that the 
base of the agent has physical size.  The result is that vertical height 
of the agent starts to go up before the 'position' (center point) of the 
agent is within the area of the ramp.  Similarly, the vertical position 
of the agent does not go down until after the position has been on the 
ramp for a couple of steps.  Finally, the agent is supported by the 
ramp when the position of the agent is over the edge of the side of the 
ramp.  

For these reasons, the logic for the ramp actions is a little complicated,
consisting of checking where the agent is (close to or over the ramp) and 
what has been happening vertically.  In particular, 'falling' is defined 
as having been on the ramp recently and the vertical distance suddenly 
going down by an amount that could not happen otherwise. 

#### Tool Actions

Count the number of times that the agent performed manipulation actions on 
a tool.  This is intended for tool tests, where the agent has to use an 
object to achieve a goal.  This counts the different types of manipulation,
inlcuding pushing, pulling, rotating, torquing, and moving. It also counts 
the number of times that they attempted to do so and failed.

#### Platform Side Correctness

For several task types that force a binary choice, such as Agent 
Identification, Spatial Elimination, Interactive Object Permanence, the 
agent needs to move off of the platform to one side or the other.  
This element of the scorecard determines whether the agent moved to
the correct side.  


#### Door Choice Correctness

For "doorcluder" task types, such as Interactive Solidity and
Interactive Support, the agent needs to choose to open one of three doors. 
This element of the scorecard determines whether the agent opened the
correct door.


## Running the Scorecard


The file ```tests/scorecard_test_ground_truth.py``` shows an example of how to run the
scorecard code:  You create a Scorecard object, passing in the scene json file
along with the json file with the MCS history output, and then tell it to score all
the parts of the scorecard:

```
scorecard = Scorecard(scene_json_filepath, ouput_json_filepath)
scorecard_dict = scorecard.score_all()
```

For testing and experimentation, you can tell it calculate the
score for particular parts of the scorecard:

```
scorecard = Scorecard(scene_json_filepath, ouput_json_filepath)
num_revisit_calc = scorecard.calc_revisiting()
```

## Testing the Scorecard

The scorecard has unit tests in ```tests/test_scorecard.py```.  Those tests
generate data on the fly to be used in the test.  

Additional unit tests are based on history files in 
```tests/test_scorecard_history_data.py```.   The data that it uses is in 
```test_data/```.  Those history files are generated by code in ```tests/test_data_generator/``` 
and the output compared  with the values in ```tests/test_data/scorecard_ground_truth.txt```.  The scene history files 
are committed and are in ```tests/test_data/gen_*.json``` files.  

When the ILE or the format of the scene file changes, the generators will 
need to be run again and the scene history files updated.  To run the scene 
generators, run ```./scorecard_generator.sh``` in 
```tests/test_data_generator/```.  

