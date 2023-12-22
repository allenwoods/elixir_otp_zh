xml version='1.0' encoding='utf-8'?



Style A ReadMe






# About This Book


Ohai, welcome! Elixir is a functional programming language built on the Erlang virtual machine. It combines the productivity and expressivity of Ruby with the concurrency and fault-tolerance of Erlang. Elixir makes full use of Erlang's powerful OTP library, which many developers consider the source of Erlang's greatness, so you can have mature, professional-quality functionality right out of the gate. Elixir's support for functional programming makes it a great choice for highly distributed event-driven applications like IoT systems.


This book respects your time and is designed to get you up to speed with Elixir and OTP with minimum fuss. However, it expects that you put in the required amount of work to grasp all the various concepts. Therefore, this book works best when you can try out the examples and experiment. If you ever get stuck, don’t fret – the Elixir community is a very welcoming one!


How the book is organized


This book has three parts, eleven chapters, and an appendix. Part 1 covers the fundamentals of Elixir and OTP.


Chapter 1 introduces Elixir, how it is different from its parent language, Erlang, compares Elixir with other languages, and use cases for Elixir and OTP.


Chapter 2 takes you on an Elixir whirlwind tour. You will write your first Elixir program, and get acquainted with language fundamentals.


Chapter 3 presents processes, the Elixir unit of concurrency. You will learn about the Actor concurrency model and how to use processes to send and receive messages. You will then put together an example program to see concurrent processes in action.


Chapter 4 introduces OTP, one of Elixir’s killer features inherited from Erlang. You will learn the philosophy behind OTP, and some of the most important parts of OTP that you will use as an Elixir programmer. You will understand how OTP behaviours work, and get to build your first Elixir/OTP application – a weather program that talks to a third-party service – using the GenServer behavior.


Part 2 covers the fault-tolerant and distribution aspects of Elixir and OTP. Chapter 5 looks at the primitives available to handle errors, especially in a concurrent setting. You will learn the unique approach that the Erlang VM takes with respect to processes crashing. You will also get to experience building your own supervisor process (that resembles the Supervisor OTP behavior), before you get to use the real thing.


Chapter 6 is all about the Supervisor OTP behavior and fault-tolerance. You will learn about Erlang's "Let it Crash" philosophy. This chapter introduces the worker pool application that uses the skills built up over the previous chapters.


Chapter 7 continues with the worker pool where we add more features to make it a more full-featured and realistic worker pool application. In the process, you will learn how to build non-trivial supervisor hierarchies and also learn how to dynamically create supervisor and worker processes.


Chapter 8 examines distribution and how it helps in load balancing. It walks you through building a distributed load balancer. Along the way, you’ll learn how to build a command line program in Elixir.


Chapter 9 continues with distribution, but this time, we look at failovers and takeovers. This is absolutely critical in any non-trivial application that has to be resilient to faults. You will build a Chuck Norris jokes service that is both fault-tolerant and distributed.


Part 3 covers type specifications, property-based testing and concurrency testing in Elixir. We will look at three tools, namely, Dialyzer, QuickCheck and Concuerror and look at examples at which these tools help us write better and more reliable Elixir code.


The appendix provides instructions to set up Erlang and Elixir on your machine.


Who should read this book


You do not have a lot of time on your hands. You want to see what the fuss is all about with Elixir, and want to get your hands on the good stuff as soon as possible.


I assume you know your way around a terminal and have some programming experience.


While having prior knowledge in Elixir and Erlang would certainly be helpful, it is by no means mandatory. However, this book is not meant to serve as a reference for Elixir. You should know how to look up documentation on your own.


You are also not averse to change. Elixir moves pretty fast. But then again, you are reading this book, so I assume that this isn’t a problem for you.


How to read this book


Front to back. This book progresses linearly, and while the earlier chapters are more or less self-contained; the later chapters build upon the previous ones. Some of the chapters might require re-reading, so don’t think that you should understand all the concepts on the first reading.


My favorite kind of programming books those that encourage you to try out the code. The concepts always seem to sink in better that way. In this book, I strive to achieve the same. Nothing beats hand-on experience. There are exercises at the end of some of the chapters. **Do them!** This book is most useful with a clear head, an opened terminal, and a desire to learn something incredibly fun and worthwhile.


Getting the example code


This code is full of examples. The latest code for the book is hosted at the GitHub repository: https://github.com/benjamintanweihao/the-little-elixir-otp-guidebook-code.


About the author


Benjamin Tan Wei Hao is a software engineer at Pivotal Labs, Singapore. Deathly afraid of being irrelevant, he is always trying to catch up on his ever-growing reading list. He enjoys going to Ruby conferences and talking about Elixir.


He is also the author of a self-published book, The Ruby Closures Book, on LeanPub. He also writes for the Ruby column of SitePoint, and tries to sneak in an Elixir article now and then. In his copious free time, he blogs at benjamintan.io.





