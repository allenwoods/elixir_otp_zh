xml version='1.0' encoding='utf-8'?



Unknown






# Part 2 Fault Tolerance, Supervision and Distribution


We've come to the part where most languages and platforms struggle to do well, namely fault tolerance and distribution. We will learn about the primitives that the Erlang VM provides to detect when processes crash.


Then we will learn about the second OTP behaviour, the Supervisor, and how to manage hierarchies of processes, and automatically take action when a process crashes. We dedicate two chapters to build a full-featured worker pool application that makes use of GenServers and Supervisors.


We examine distribution through the lens of load balancing and fault-tolerance in the next two chapters that follow.


By the end of these two chapters, you would have built a distributed load tester, a distributed and fault-tolerant Chuck Norris jokes service. More importantly, you would have a firm grasp of how to use OTP effectively.





