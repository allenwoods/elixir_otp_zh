xml version='1.0' encoding='utf-8'?



Style A ReadMe





# Appendix A Installing Erlang and Elixir


Welcome to Chapter 0, or what publishers like to call, Appendix *A*. We will cover how to get Elixir set up on your system as fast as possible. I will cover Mac OS X, some Linux distributions and MS Windows. It is listed in order of difficulty.


A.1          Getting Erlang


Before we install Elixir, we must Erlang. At this time of writing, the minimum version of Erlang is 18.0. Elixir has so far been very good at keeping up with new Erlang releases.


Just as there are multiple ways of getting Elixir, the same goes to Erlang. If you can get it via a package manager, do that. Otherwise, the least problematic way (by far!) is to head over to the Erlang Solutions site[[1]](#uGRexWD7e8DL2GrOrcFocH8) and download a copy. They host Erlang packages for several Linux distributions (Ubuntu, CentOS, Debian, Fedora and even one of the Raspberry Pi), Mac OS X and Windows.


A.2          Method 1: Package Managers / Pre-built installers.


If you operating system comes with it, you should always opt to install Elixir via a package manager. That would usually get you up to speed in the shortest time possible. The following sections outline the installation steps for some of the more populate operating systems. If you system is not listed, don’t fret. There are usually instructions floating around cyberspace.


A.2.1       Mac OS X via Homebrew and Macports


Chances are you would either have the Homebrew or Macports package manager installed. If so, then you are only one step away from a new and shiny Elixir (and Erlang) installation. For Homebrew:

`% brew update && brew install elixir`
For Macports, just do the usual
`port install`:

`% sudo port install elixir`
Notice that we are not specifying any version numbers. Installing via package managers usually installs the latest *stable* versions. We will cover how to build and install Elixir from source in the later sections.


A.2.2       Linux (Ubuntu and Fedora)


Since there are a billion Linux distributions out there, I will limit it to the more popular ones, namely Ubuntu and Fedora. If so, installing Elixir would be a one-liner affair for you.


Fedora 17 to 22 (and newer)


If you are on Fedora 17 and newer (and older than Fedora 21):

`% yum install elixir`
If you are on Fedora 22 and above:

`% dnf install elixir`
Ubuntu


Ubuntu-flavored distributions need to do slightly more work. You first need to add the Erlang solutions repository:

`% wget https://packages.erlang-solutions.com/erlang-solutions_1.0_all.deb && sudo dpkg -i erlang-solutions_1.0_all.deb`
Next, as all Ubuntu users would already know:

`% sudo apt-get update`
Next, we need to get Erlang (and a bunch of other Erlang related applications):

`% sudo apt-get install esl-erlang`
Finally, we can grab Elixir:

`% sudo apt-get install elixir`
A.2.3       MS Windows


Getting Elixir on Windows couldn’t be easier. All you need to do is to install the Elixir web installer[[2]](#unSboXWaDHFFHWhG44f39C3), and you should be set.


A.3          Method 2: Compiling from scratch (Linux/Unix only)


So, you are feeling lucky eh? Sometimes there’s just that awesome feature that you cannot wait to play with. There are times where you want to experiment with Elixir directly and maybe fix a bug or implement a new feature. If so, then this is the route you want to take.


Happily, the only thing Elixir has a dependency on is Erlang. If you have installed Erlang properly, compiling Elixir from source is usually not very dramatic.


In the section, I assume that you are using a Unix/Linux system and have all the necessary build tools installed, such as
`make`. First, you need to clone Elixir from the official repository:

`% git clone https://github.com/elixir-lang/elixir.git`
Next, change into the newly created directory:

`% cd elixir`
Finally, you can start building the sources:

`% make clean test`
It is pretty fascinating to see all the messages go by – it never gets old. Once done, there’s an additional step: You need to add the
`elixir`
directory to your
`PATH`, so that you can access commands like
`elixir`
and
`iex`.


Depending on your shell, you can append the
`elixir`
directory to your
`PATH`. For example, if I were to use
`zsh`, then I would locate the
`~/.zshrc`
and append the directory:

`export PATH= ... # other PATH goes there export PATH=$PATH:"~/elixir"`
Here, I am specifying that the one of the
`PATH`s is the
`elixir`
directory is located directly under my home directory.


A.4          Verifying your Elixir installation


The last thing to do is checking that Elixir has been installed correctly:

`% elixir -v`
If all goes well, you will be greeted with the Erlang/OTP version and the Elixir version:

`Erlang/OTP 18 [erts-7.2] [source] [64-bit] [smp:4:4] [async-threads:10] [hipe] [kernel-poll:false] [dtrace]  Elixir 1.3.2`
What are you waiting for? On to chapter 1!





[****[1]****](#ulZ3weFoR2csTrcsjKXzrfG) https://www.erlang-solutions.com/resources/download.html




[****[2]****](#uVJT5MoKQk8Ut7nrzybS9dC) https://repo.hex.pm/elixir-websetup.exe





