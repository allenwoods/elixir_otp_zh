xml version='1.0' encoding='utf-8'?



Style A ReadMe





# 3   Processes 101


This chapter covers:


·      The Actor concurrency model


·      Creating processes


·      How to send and receive messages using processes


·      Achieving concurrency using processes


·      How to make processes communicate with each other


The concept of processes is one of the most important to understand, and rightly deserves its own chapter. Processes are the fundamental unit of concurrency in Elixir. In fact, the Erlang VM supports up to 134 million[[1]](#upz6AcFmGwE9eU3xCl8oqRD) (!) processes, causing all your CPUs to happily light up. I always get a warm, fuzzy feeling knowing that I am getting my money's worth in hardware. The processes created by the Erlang VM are independent of the operating system. The processes created by the Erlang VM are much more lightweight, and only take mere microseconds to create[[2]](#ufy3ItmzNMRjmsqbWuxUpMA).


We are going to embark on a fun project. In this chapter, we will build a simple program that reports the temperature of a given city/state/country. But first, let us learn about the actor concurrency model.


3.1            Actor Concurrency Model


Erlang (and therefore Elixir) uses the Actor Concurrency Model. This means that:


1.  Each *actor* is a *process*.


2.  Each process performs a *specific task*.


3.  To tell a process to do something, you need to *send it a message*. The process can also reply by *sending back another message*.


4.  The kinds of messages the process can act upon are specific to the process itself. In other words, messages are *pattern matched*.


5.  Other than that, processes *do not share any information* with other processes.


If all this seems fuzzy now, fret not. If you have done any object-oriented programming, you will find that processes resemble objects in many ways. You could even argue that it is a purer form of object-orientation.


Here is one way to think about actors. Actors are just like people. We communicate each other by talking to each other. For example, my wife tells me to do the dishes. Of course, I respond by doing the dishes – I’m a good husband. If however, my wife tells me to eat my vegetables, she will get ignored – I won’t respond to that. In effect, I’m choosing to respond to only certain kinds of messages. Finally, I don’t know what goes on inside her head, and neither does she know what goes on inside my head. As you will soon see, the actor concurrency model acts just like that – responding to only certain kinds of messages.


3.2            Building a Weather application


Conceptually, our application is pretty simple. The first version accepts a single argument containing a location, and it reports the temperature in Celsius. That involves making a HTTP request to an external weather service, and parsing the JSON response to extract the temperature.


![](../Images/3_1.png)  



Figure 3.1 Weather actor handling a single request.


Making a single request is trivial. What happens if we wanted to find out the temperatures of 100 cities at once? Assuming that each request takes 1 second, are we going to wait for 100 seconds? Obviously not! We will see how we can make concurrency requests so that we can get our results as soon as possible.


One of the properties of concurrency is that we never know which order the responses come in. For example, imagine that I pass in a list of cities in alphabetical order. The responses I get back are in no way guaranteed to be in the same order.


How could we ensure that the responses are in the correct order then? Read on, dear reader, because we begin our meteorological adventures in Elixir right now.


3.2.1                      The Naïve Version


We start with a naïve version. That is, no concurrency will be involved. On the other hand, the naïve version will contain all of the logic needed to make a request, parse the response, and return the result. By the end of this iteration, you would learn how to:


·      Install and make use of third-party libraries using mix


·      Make a HTTP request to a third party API


·      Parse a JSON response using pattern matching


·      See how pipes facilitate data-transformation


This will be the first non-trivial program that you will be working through. But no worries though, you will be guided along every step of the way. Let’s begin!


Creating a New Project


The first order of business is to create a new project, and more importantly, give it a great name. Since I’m the author, I get to choose the name. In listing 3.1, we use
`mix new <project name>`
to create a new project


Listing 3.1 Creating a new project

`% mix new metex`
`* creating README.md`
`* creating .gitignore`
`* creating mix.exs`
`* creating config`
`* creating config/config.exs`
`* creating lib`
`* creating lib/metex.ex`
`* creating test`
`* creating test/test_helper.exs`
`* creating test/metex_test.exs`
`Your mix project was created successfully.`
`You can use mix to compile it, test it, and more:`

`cd metex`
`mix test`
`% cd metex`
Follow the instructions and
`cd`
into the
`metex`
directory.


Installing the Dependencies


Open
`mix.exs`. This is what you will see:


Listing 3.2 The default generated mix.exs file.

`defmodule Metex.Mixfile do`
`use Mix.Project`

`def project do`
`[app: :metex,`
`version: "0.0.1",`
`elixir: "~> 1.0",`
`deps: deps]`
`end`

`def application do`
`[applications: [:logger]]`
`end`

`defp deps do`
`[]`
`end``end`
Every project generated by
`mix`
will contain this file. It consists of two public functions,
`project`
and
`application`. The
`project`
function basically sets up our project. More importantly, it sets up our project’s dependencies by invoking the
`deps`
private function. As it stands,
`deps`
is an empty list – for now. The
`application`
function is used to generate an application resource file. Certain dependencies in Elixir require them to be started up in a specific way. Dependencies that are like that are declared within this function. For example, before our application starts, the
`logger`
application is started up first.


Let’s add two dependencies by modifying the
`deps`
function to look like (listing 3.3):


Listing 3.3 Declaring dependencies in mix.exs

`defp deps do`
`[`
`{:httpoison, "~> 0.9.0"},  #1`
`{:json,      "~> 0.3.0"}   #1`
`]``end`
#1 declaring the dependencies and also specifying the respective version numbers


Next, add an entry to the
`application`
function:

`def application do`
`[applications: [:logger, :httpoison]]``end`
How did I know that I should include
`:httpoison`, and not say,
`:json`? Truth is, I don’t. So I always do the next best thing – read the fine manual. Each time I install a library, I first take a look at the README. In
`:httpoison`’s case, the README clearly states:


![](../Images/3_2.png)  



Figure 3.2 It is always helpful to look at the README of third-party libraries for important installation instructions.



Dependency version numbers are important!



Pay attention to the version numbers of your dependencies. Using the wrong version number could result in puzzling errors. Another thing to take note of is that many of these libraries will specify the minimum version of Elixir that it is compatible with.



 



Making sure you are in the Metex directory, we can install our dependencies using the
`mix deps.get`
command:

`% mix deps.get`
Notice that
`mix`
helpfully resolves dependencies too. In this case, it brought in two other libraries, hackney and idna (listing 3.4):


Listing 3.4 mix resolves dependencies automatically

`% mix deps.get`
`Running dependency resolution`
`* Getting httpoison (Hex package)`
`Checking package (http://s3.hex.pm.global.prod.fastly.net/tarballs/httpoison-0.9.0.tar)`
`Using locally cached package`
`* Getting json (Hex package)`
`Checking package (http://s3.hex.pm.global.prod.fastly.net/tarballs/json-0.3.2.tar)`
`Using locally cached package`
`* Getting hackney (Hex package)`
`Checking package (http://s3.hex.pm.global.prod.fastly.net/tarballs/hackney-1.5.7.tar)`
`Using locally cached package`
`* Getting ssl_verify_fun (Hex package)`
`Checking package (http://s3.hex.pm.global.prod.fastly.net/tarballs/ssl_verify_fun-1.1.0.tar)`
`Using locally cached package`
`* Getting mimerl (Hex package)`
`Checking package (http://s3.hex.pm.global.prod.fastly.net/tarballs/mimerl-1.0.2.tar)`
`Using locally cached package`
`* Getting metrics (Hex package)`
`Checking package (http://s3.hex.pm.global.prod.fastly.net/tarballs/metrics-1.0.1.tar)`
`Using locally cached package`
`* Getting idna (Hex package)`
`Checking package (http://s3.hex.pm.global.prod.fastly.net/tarballs/idna-1.2.0.tar)`
`Using locally cached package`
`* Getting certifi (Hex package)`
`Checking package (http://s3.hex.pm.global.prod.fastly.net/tarballs/certifi-0.4.0.tar)``Using locally cached package`
3.3            The Worker


Before we get into the implementation for the worker, we need to obtain an API key from the third-party weather service, OpenWeatherMap. Head over to
`http://openweathermap.org/`
to create an account. Once done, you will see that your API key has been created for you:


![](../Images/3_3.png)  



Figure 3.3 Creating an account and getting an API key from OpenWeatherMap.


Now we can get into the implementation details of the worker. The worker’s job is do fetch the temperature of a given location from OpenWeatherMap, and parse the results. Create
`worker.ex`
in the
`lib`
directory. Here is the entire listing for the worker (listing 3.5):


Listing 3.5 The full source of worker.ex. Save this in lib/worker.ex.

`defmodule Metex.Worker do`

`def temperature_of(location) do`
`result = url_for(location) |> HTTPoison.get |> parse_response`
`case result do`
`{:ok, temp} ->`
`"#{location}: #{temp}°C"`
`:error ->`
`"#{location} not found"`
`end`
`end`

`defp url_for(location) do`
`location = URI.encode(location)`
`"http://api.openweathermap.org/data/2.5/weather?q=#{location}&appid=#{apikey}"`
`end`

`defp parse_response({:ok, %HTTPoison.Response{body: body, status_code: 200}}) do`
`body |> JSON.decode! |> compute_temperature`
`end`

`defp parse_response(_) do`
`:error`
`end`

`defp compute_temperature(json) do`
`try do`
`temp = (json["main"]["temp"] - 273.15) |> Float.round(1)`
`{:ok, temp}`
`rescue`
`_ -> :error`
`end`
`end`

`defp apikey do`
`“APIKEY-GOES-HERE”`
`end`
`end`
Do not be alarmed if you don't understand entire what is going on. We will go through the program bit by bit. For now, let's see how we can run this program from
`iex`. From the project root directory, launch
`iex`
like so:

`% iex –S mix`
If it is the first time you are running that command, you will notice a list of dependencies being compiled. You will not see this the next time you run
`iex`, unless you modify the dependencies. Now, let's find out the temperatures of some of the coldest places in the world (listing 3.6):


Listing 3.6 An example run of the worker. (Interactive Elixir)

`iex(1)> Metex.Worker.temperature_of "Verkhoyansk, Russia"`
`"Verkhoyansk, Russia: -37.3°C"`
Just for kicks, let's try another:

`iex(2)> Metex.Worker.temperature_of "Snag, Yukon, Canada"`
`"Snag, Yukon, Canada: -27.6°C"`
What happens when we give a nonsensical location?

`iex(3)> Metex.Worker.temperature_of "Omicron Persei 8"`
`"Omicron Persei 8 not found"`
Now that we have see the worker in action, let's take a closer look and figure out how it works. We begin with the
`temperature_of/1`
function in listing 3.7:


Listing 3.7 The core of Metex.Worker – temperature\_of/1 function

`defmodule Metex.Worker do`

`def temperature_of(location) do`
`result = url_for(location) |> HTTPoison.get |>  parse_response #1`
`case result do`
`{:ok, temp} ->                          #2`
`"#{location}: #{temp}°C"              #2`
`:error ->                               #3`
`"#{location} not found"               #3`
`end`
`end`

`# ...``end`
#1 Data transformation: From URL to HTTP response to parsing that response


#2 A successfully parsed response returns the temperature and location


#3 Otherwise, an error message is returned


The most important line in the entire function is

`result = location |> url_for |> HTTPoison.get |> parse_response`
Without using the pipe operator, we would have to write our function like so:

`result = parse_response(HTTPoison.get(url_for(location)))`
The
`location |> url_for`
constructs the URL that is used to call the weather API. For example, the URL for Singapore would be (substitute
`<APIKEY>`
with your own):

`http://api.openweathermap.org/data/2.5/weather?q=Singapore&appid=<APIKEY>`
Once we have the URL, we can then make use of httpoison, a HTTP client, to make a GET request:

`location |> url_for |> HTTPoison.get`
If you tried that URL in your browser, you would have gotten something like this (I've trimmed the JSON for brevity):

`{`
`...`
`"main": {`
`"temp": 299.86,`
`"temp_min": 299.86,`
`"temp_max": 299.86,`
`"pressure": 1028.96,`
`"sea_level": 1029.64,`
`"grnd_level": 1028.96,`
`"humidity": 100`
`},`
`...``}`
Let's take a closer look at the response of the HTTP client. Try this out in iex too. In case you exited iex, remember to use 
`iex -S mix`
so that the dependencies (such as httpoison) are loaded properly.


We can try out the URL of Singapore's temperature (listing 3.8):


Listing 3.8 Using HTTPoison to make a GET request (Interactive Elixir)

`iex(1)> HTTPoison.get "http://api.openweathermap.org/data/2.5/weather?q=Singapore&appid=<APIKEY>"`
Take a look at the results:

`{:ok,`
`%HTTPoison.Response{body: "{\"coord\":{\"lon\":103.85,\"lat\":1.29},\"sys\":{\"message\":0.098,\"country\":\"SG\",\"sunrise\":1421795647,\"sunset\":1421839059},\"weather\":[{\"id\":802,\"main\":\"Clouds\",\"description\":\"scattered clouds\",\"icon\":\"03n\"}],\"base\":\"cmc stations\",\"main\":{\"temp\":299.86,\"temp_min\":299.86,\"temp_max\":299.86,\"pressure\":1028.96,\"sea_level\":1029.64,\"grnd_level\":1028.96,\"humidity\":100},\"wind\":{\"speed\":6.6,\"deg\":29.0007},\"clouds\":{\"all\":36},\"dt\":1421852665,\"id\":1880252,\"name\":\"Singapore\",\"cod\":200}\n",`
`headers: %{"Access-Control-Allow-Credentials" => "true",`
`"Access-Control-Allow-Methods" => "GET, POST",`
`"Access-Control-Allow-Origin" => "*",`
`"Connection" => "keep-alive",`
`"Content-Type" => "application/json; charset=utf-8",`
`"Date" => "Wed, 21 Jan 2015 15:59:14 GMT", "Server" => "nginx",`
`"Transfer-Encoding" => "chunked", "X-Source" => "redis"},``status_code: 200}}`
What about passing in a URL to a missing page?

`iex(2)> HTTPoison.get "http://en.wikipedia.org/phpisawesome"`
This will return something like:

`{:ok,`
`%HTTPoison.Response{body: "<html>Opps</html>",`
`headers: %{"Accept-Ranges" => "bytes", "Age" => "12",`
`"Cache-Control" => "s-maxage=2678400, max-age=2678400",`
`"Connection" => "keep-alive", "Content-Length" => "2830",`
`"Content-Type" => "text/html; charset=utf-8",`
`"Date" => "Wed, 21 Jan 2015 16:04:48 GMT",`
`"Refresh" => "5; url=http://en.wikipedia.org/wiki/phpisawesome",`
`"Server" => "Apache",`
`"Set-Cookie" => "GeoIP=SG:Singapore:1.2931:103.8558:v4; Path=/; Domain=.wikipedia.org",`
`"Via" => "1.1 varnish, 1.1 varnish, 1.1 varnish",`
`"X-Cache" => "cp1053 miss (0), cp4016 hit (1), cp4018 frontend miss (0)",`
`"X-Powered-By" => "HHVM/3.3.1",`
`"X-Varnish" => "2581642697, 646845726 646839971, 2421023671",`
`"X-Wikimedia-Debug" => "prot=http:// serv=en.wikipedia.org loc=/phpisawesome"},``status_code: 404}}`
And finally, a ridiculous URL yields:


Listing 3.9 Using HTTPoison to make an invalid GET request (Interactive Elixir)

`iex(3)> HTTPoison.get "phpisawesome"`
`{:error, %HTTPoison.Error{id: nil, reason: :nxdomain}}`
We have just seen at least three variations of the what HTTPoison.get(url) can return. The happy path returns a *pattern* that resembles

`{:ok, %HTTPoison.Response{status_code: 200, body: content}}}`
The pattern above conveys the following information:


·      This is a two-element tuple


·      The first element of the tuple is an
`:ok`
atom, followed by a structure that represents the response


·      The response is of type
`HTTPoison.Response`
that contains at least two fields


·      The value of
`status_code`
is 200, which represents a successful HTTP GET request


·      The value of body is *captured* in content


As you can see, pattern matching is incredibly succinct, and a beautiful way to express what you want. Similarly, an error tuple has the following pattern:

`{:error, %HTTPoison.Error{reason: reason}}`
Let's do the same analysis again:


·      This is a two-element tuple


·      The first element of the tuple is an
`:error`
atom, followed by a structure that represents the error


·      The response is of type
`HTTPoison.Error`
that contains at least one fields, reason


·      The reason of the error is captured in
`reason`


With all that in mind, let's take a look at the
`parse_response/1`
function (listing 3.11):


Listing 3.11 Pattern matching in the parse\_response/1 function

`defp parse_response({:ok, %HTTPoison.Response{body: body, status_code: 200}}) do`
`body |> JSON.decode! |> compute_temperature`
`end`

`defp parse_response(_) do`
`:error``end`
Here, we specify two versions of
`parse_response/1.`
The first version matches a successful GET request, because we are matching a response that is of type
`HTTPoison.Response,`
and also making sure that the
`status_code`
is 200. Otherwise, we treat any other kind of response as an error. Let's take a closer look now at the first version of
`parse_response/1.`

`defp parse_response({:ok, %HTTPoison.Response{body: body, status_code: 200}}) do`
`# ...``end`
Upon a successful pattern match, the string representation of the JSON is captured in the body variable. In order to turn it into a "real" JSON, we need to decode it:

`body |> JSON.decode!`
We then pass this JSON into the
`compute_temperature/1`
function. Here's the function again:

`defp compute_temperature(json) do`
`try do`
`temp = (json["main"]["temp"] - 273.15) |> Float.round(1)`
`{:ok, temp}`
`rescue`
`_ -> :error`
`end``end`
We wrap the computation in a
`try … rescue … end`
block. We attempt to retrieve the temperaure from the given JSON and then perform some arithmetic. At any of these points an error could occur. If it does, we want the return result to be an
`:error atom.`
Otherwise, a two-element tuple containing
`:ok`
as the first element and the temperature is returned. Having return values of different “shapes” is very useful because code that calls this function for example can easily pattern match on both success and failure cases. You will see many more cases where we can exploit opportunities for pattern matching in the following chapters.


Here, we are subtracting 273.15 because the API provides the results in Kelvins. We also round off the temperature to one decimal place.


What happens if the HTTP GET response doesn't match the first pattern? That's the job of the second
`parse_response/1`
function:


Listing 3.11 This version of parse\_response/1 matches any message.

`defp parse_response(_) do`
`:error``end`
Here, any other response other than a successful one is treated as an error. That is basically it! You should now have a better understanding of how to the worker works. Let's learn about how processes are created in Elixir.


3.4            Creating Processes for Concurrency


Let's imagine we have a list of cities we want to get temperatures of:


Listing 3.12 Creating a list of cities (Interactive Elixir)

`iex> cities = ["Singapore", "Monaco", "Vatican City", "Hong Kong", "Macau"]`
Next, we send each request to the worker, one at a time:


Listing 3.13 Making a request to find the temperature of a city, one at a time (Interactive Elixir)

`iex(2)> cities |> Enum.map(fn city ->`
`Metex.Worker.temperature_of(city)``end)`
This results in:

`["Singapore: 27.5°C", "Monaco: 7.3°C", "Vatican City: 10.9°C", "Hong Kong: 18.1°C", "Macau: 19.5°C"]`
The problem with this approach is that it is *wasteful*. As the size of the list grows, so will the time needed to wait for all the responses to complete. The only time the next request will be processed is when the one before it has completed. We can do better.


![](../Images/3_2a.png)  



Figure 3.2 Without concurrency, the next request will have to wait for the previous one to complete. This is very inefficient.


One important thing to realise is that *each request does not depend on the other*. In other words, we can package each call to
`Metex.Worker.temperature_of/1`
into a process. Let's teach our worker how to respond to messages. First, add the
`loop/0`
function into
`lib/worker.ex:`


Listing 3.14  Adding the loop/0 function into the worker so that it can respond to messages.

`defmodule Metex.Worker do`

`def loop do`
`receive do`
`{sender_pid, location} ->`
`send(sender_pid, {:ok, temperature_of(location)})`
`_ ->`
`IO.puts "don't know how to process this message"`
`end`
`loop`
`end`

`defp temperature_of(location) do`
`# ...`
`end`

`# ...``end`
Before we go into the details, let's play around with this. If you already have iex opened, you can *reload* the module:

`iex> r(Metex.Worker)`
Otherwise, you can run
`iex -S mix`
again. First, we create a process that runs the worker's loop function:

`iex> pid = spawn(Metex.Worker, :loop, [])`
The built-in spawn function creates a process. There are two variations of spawn. The first version takes in a single function as a parameter, the second one takes in a given module and function passing the given arguments. Both versions return a *process id*, or *pid*, as the result.


3.4.1                      Receiving Messages


A pid is a *reference* to a process, much like how in object-oriented programming the result on initialising an object gives you a *reference* to that object. With the pid, we can send the process *messages*. The kinds of messages that the process can receive is defined within the receive block (listing 3.15):


Listing 3.15 The kinds of messages a process can receive is defined in the receive block.

`receive do`
`{sender_pid, location} ->`
`send(sender_pid, {:ok, temperature_of(location)})`
`_ ->`
`IO.puts "don't know how to process this message"``end`
Messages are pattern-matched from *top to bottom*. In this case, if the incoming message is a two-element tuple, then the body will be executed. Any other message will be pattern-matched in the second pattern.


What happens if were were to write the above piece of code with the function clauses swapped (listing 3.16):


Listing 3.16 Pattern matching occurs top-to-bottom.  Swapping the order of messages received matters!

`receive do`
`_ ->                                  #1`
`IO.puts "don't know how to process this message"`
`{sender_pid, location} ->`
`send(sender_pid, {:ok, temperature_of(location)})``end`
#1 This matches any message!


If you try to run this, Elixir helpfully warns you:

`lib/worker.ex:7: warning: this clause cannot match because a previous clause at line 5 always matches`
In other words, the
`{sender_pid, location}`
will *never* be matched because the match-all operator (“`_”`), as it name suggests, will *greedily* match every single message that comes its way.


In general, it is good practice to have the match-all case as the last message to be matched. This is because unmatched messages in kept in the mailbox. Therefore, it is possible to make the VM run out of memory by repeatedly sending messages to a process that doesn't handle unmatched messages.


3.4.2                      Sending Messages


Messages are sent using the built-in
`send/2`
function. The first argument is the pid of the process you want to send the message to. The second argument is the actual message.


Listing 3.17 The pattern of the message that the worker can receive

`receive do`
`{sender_pid, location} ->               #1`
`send(sender_pid, {:ok, temperature_of(location)})``end`
#1 The incoming message contains the sender pid and location


Here, we are sending the result of the request to
`sender_pid`. Where do we get
`sender_pid`? The incoming message, of course! If you look closely, we are expecting that the incoming message consists of the sender's pid and the location. Putting in the sender's pid (or any process id for that matter) is like putting a *return address* at the back of the envelope. It provides the recipient an avenue to reply to.       


Let's send the process that we have created earlier a message (listing 3.18):


Listing 3.18 Sending the process a message using send/2 (Interactive Elixir)

`iex> send(pid, {self, "Singapore"})`
Results in

`{#PID<0.125.0>, "Singapore"}`
Wait, besides the return result, nothing else happened! Let's break it down a little. The first thing to note is that the result of
`send/2`
is always the *message*. The second thing is that
`send/2`
always returns immediately. In order words,
`send/2`
is like fire-and-forget. So that explains how we got the result. But what about *why* we are not getting back any results?


What did we pass into the message payload as the sender pid?
`self`! What is
`self`
exactly?
`self`
is the pid of the calling process. In this case, it is the pid of the
`iex`
shell session.  We are effectively telling the worker to send all replies to the shell session. To get back responses from the shell session, we can use the built-in
`flush/0`
function (listing 3.19):


Listing 3.19 Retrieving messages sent to the shell process using flush/0 (Interactive Elixir)

`iex> flush`
`"Singapore: 27.5°C"``:ok`
`flush/0`
clears out all the messages that were sent to the shell and prints them out. Therefore, the next time you do another
`flush`, you will only get the
`:ok`
atom. Let's see this in action. Once again, we have a list of cities:

`iex> cities = ["Singapore", "Monaco", "Vatican City", "Hong Kong", "Macau"]`
Then, we iterate through each city. In each iteration, we spawn a new worker. Using the pid of the new worker, we send it a two-element tuple as a message containing the return address (the
`iex`
shell session) and the city (listing 3.20):


Listing 3.20 For each city, spawn a process to find out the temperature of that city (Interactive Elixir)

`iex> cities |> Enum.each(fn city ->`
`pid = spawn(Metex.Worker, :loop, [])`
`send(pid, {self, city})``end)`
Now, let's flush the messages:

`iex> flush`
`{:ok, "Hong Kong: 17.8°C"}`
`{:ok, "Singapore: 27.5°C"}`
`{:ok, "Macau: 18.6°C"}`
`{:ok, "Monaco: 6.7°C"}`
`{:ok, "Vatican City: 11.8°C"}``:ok`
Awesome! We finally got back our result. Notice that the result are *not* in any order. That's because which response that completed first could send the reply back to the sender as soon as it was done. If you run the iteration again, you would most probably get the results in a different order.


![](../Images/3_4.png)  



Figure 3.4 The order of sent messages in not guaranteed when processes do not have to wait for each other.


Take a look at the
`loop`
function again. The first thing to notice is that it is recursive – it calls itself after a message has been processed:

`def loop do`
`receive do`
`{sender_pid, location} ->`
`send(sender_pid, {:ok, temperature_of(location)})`
`_ ->`
`send(sender_pid, "Unknown message")`
`end`
`loop # 1``end`
#1 Recursive call to loop


You might be wondering why we needed the loop in the first place. In general, the process should be able to handle more than one message. If we left the recursive call out, the moment the process handles that first (and only) message, it will exit, and get garbage collected. We usually want our processes to be able to handle more than one process! Therefore, we need a recursive call to the message handling logic.


3.5      Collecting and Manipulating Results with Another Actor


Sending results to the shell session is great for seeing what messages are sent by the workers, but nothing more. If we want to manipulate the results, say, sorting them, we need to find another way. Instead of using the shell session as the sender, we can create another actor to collect the results.


This means that this actor must keep track of *how many* messages are expected. In other words, the actor must keep state. How could we do that?


Let's set up the actor first. Create a file called
`lib/coordinator.ex`
and fill it up as in listing 3.21:


Listing 3.21 The full source of coordinator.ex. Save this in lib/coordinator.ex.

`defmodule Metex.Coordinator do`

`def loop(results \\ [], results_expected) do`
`receive do`
`{:ok, result} ->`
`new_results = [result|results]`
`if results_expected == Enum.count(new_results) do`
`send self, :exit`
`end`
`loop(new_results, results_expected)`
`:exit ->`
`IO.puts(results |> Enum.sort |> Enum.join(", "))`
`_ ->`
`loop(results, results_expected)`
`end`
`end`
`end`
Let's see how we can use the coordinator together with the workers. Open up
`lib/metex.ex`, and enter the following (listing 3.22):


Listing 3.22 A function to spawn a coordinator process and worker processes in lib/metex.ex.

`defmodule Metex do`

`def temperatures_of(cities) do`
`coordinator_pid =`
`spawn(Metex.Coordinator, :loop, [[], Enum.count(cities)]) #1`

`cities |> Enum.each(fn city ->                   #2`
`worker_pid = spawn(Metex.Worker, :loop, [])    #3`
`send worker_pid, {coordinator_pid, city}       #4`
`end)`
`end`
`end`
#1 Create a coordinator process


#2 Iterate through each city


#3 Create a worker process and execute its loop function


#4 Send the worker a message containing the coordinator process pid and city


We can then find out the temperatures of cities by first creating a list of cities

`iex> cities = ["Singapore", "Monaco", "Vatican City", "Hong Kong", "Macau"]`
Followed by calling Metex.temperatures\_of/1:

`iex> Metex.temperatures_of(cities)`
The result is as expected:

`Hong Kong: 17.8°C, Macau: 18.4°C, Monaco: 8.8°C, Singapore: 28.6°C, Vatican City: 8.5°C`
Here is how
`Metex.temperatures\_of/1`
work. Firstly, we create a coordinator process. The loop function of the coordinator process expects two arguments, the current collected results and the total number of results it expects. Therefore, when we first create the coordinator, we initialize it with an initially empty result list , and the number of cities:

`iex> coordinator_pid = spawn(Metex.Coordinator, :loop, [[], Enum.count(cities)])`
Now we have the coordinator process waiting for messages from the worker. Given a list of cities, we iterate through each city, create a worker then send the worker a message containing the coordinator pid and the city.


Listing 3.23 Spawn worker processes for each city, and set the coordinator process as the recipient of messages from the workers. (Interactive Elixir)

`iex> cities |> Enum.each(fn city ->`
`worker_pid = spawn(Metex.Worker, :loop, [])`
`send worker_pid, {coordinator_pid, city}``end)`
Once all five workers have completed the requests, the coordinator will dutifully report the result:

`Hong Kong: 16.6°C, Macau: 18.3°C, Monaco: 8.1°C, Singapore: 26.7°C, Vatican City: 9.9°C`
Success! Notice that the results are sorted in lexicographical order. Now it is time to dig into the coordinator process and find out how it works.


What kinds of messages can the coordinator receive from the worker? Inspecting the
`receive do ... end`
block, we can conclude there are at least two kinds we are especially interested in:


`·`
`{:ok, result}`


`·`
`:exit`


Other kinds of messages are ignored. Let's examine each kind of message in closer detail.


3.5.1                      {:ok, result} – The Happy Path Message - {:ok, result}


This is the "happy path" message that we expect from a worker if nothing went wrong (listing 3.24):


Listing 3.24 The happy path message

`def loop(results \\ [], results_expected) do`
`receive do`
`{:ok, result} ->`
`new_results = [result|results]                    #1`
`if results_expected == Enum.count(new_results) do #2`
`send self, :exit                                #3`
`end`
`loop(new_results, results_expected)               #4`

`# ... other patterns omitted ...`

`end``end`
#1 Add result to current list of results


#2 Check if all results have been collected


#3 Send the coordinator the exit message


#4 Loop with new results. Notice that results\_expected remains unchanged


When the coordinator receives a message that fits the
`{:ok, result}`
pattern, it first adds the result into the current list of results.


![](../Images/3_5.png)  



Figure 3.5 When the first result comes in, the actor saves the result in a list.


Next, we check if the coordinator has received the correct number of results expected. Let’s assume not. In this case, the loop function calls itself again. Notice the arguments to the recursive call to loop. This time we pass in
`new\_results`, while
`results\_expected`
remains unchanged.


![](../Images/3_6.png)  



Figure 3.6 When the coordinator receives the next message, it stores it in the results list again.


This is how state is kept in an actor. The *copy* of the arguments are modified, and then passed along into the loop function, where it would be available during the next function call to itself.


3.5.2                      :exit – The Poison Pill Message


When the coordinator has received all the messages, it must find a way to tell itself to stop, and report the results if necessary. A simple way to do this is via a "poison pill" message (listing 3.25).


![](../Images/3_7.png)  



Figure 3.7 When the coordinator receives the :exit message, it returns the results in alphabetical order, and then exits.


Note that the
`:exit`
message  by itself is not special. You can call it
`:kill`,
`:self\_destruct`, or
`:kaboom`.


When the coordinator receives an
`:exit`
message, it prints out the results lexicographically that are separated by commas. Since we want to coordinator to exit, we do not have to call the
`loop`
function (listing 3.25).


Listing 3.25 The poison pill message

`def loop(results \\ [], results_expected) do`
`receive do`
`# ... other pattern omitted ...`

`:exit ->`
`IO.puts(results |> Enum.sort |> Enum.join(", ")) #1`

`# ... other pattern omitted ...`
`end``end`
#1 Print the results lexicographically, separated by commas


3.5.3                      Any Other Messages


Finally, we must take care of any other types of messages that the coordinator can potentially receive. We capture these unwanted messages with the
`\_`
operator. Finally, we need to remember to loop again, although we leave the arguments unmodified (listing 3.26):


Listing 3.26 Matching all other messages

`def loop(results \\ [], results_expected) do`
`receive do`
`# ... other patterns omitted ...`
`_ ->                                #1`
`loop(results, results_expected)   #2`
`end``end`
#1 Match every other kind of messages


#2 Loop again, leaving the arguments unmodified


3.5.4                      The Bigger Picture


Congratulations – You have just written you first concurrent program in Elixir! You used multiple processes to perform computations concurrently. None of the processes had to wait for each other while performing the computation, except for the coordinator process.


An important point to reinforce is that there is no shared memory. The only way a change of state could occur within a process is when a message is sent to it. This is different from threads, because threads share memory. This means that multiple threads can modify the same memory, an endless source of concurrency bugs (and headaches).


When designing your own concurrent programs, it is important to decide the types of messages that the processes should receive and send, along with the interations between processes. In our example program, I decided to use
`{:ok, result}`
and
`:exit`
for the coordinator process, and
`{sender_pid, location}`
for the worker process. I have personally found it very helpful to sketch out the interactions between the various processes along with the messages that are being sent and received. Resist the temptation to dive right into coding and spend a few minutes sketching. Doing this will save you hours of head-scratching and cursing!


3.6            Exercises


Processes are fundamental to Elixir. You will gain a better understanding only by running and experimenting with the code.


1.   Read the documentation for
`send`
and
`receive`. For
`send`, find out what are valid destinations that you can send messages to. For
`receive`, study the example that the documentation provides.


2.  Read the documentation for
`Process`.


3.  Write a program that spawns two processes. The first process, on receiving a
`ping`
message, replies with a
`pong`
message. The second process, on receiving a
`pong`, message replies with a
`ping`
message to the sender.


3.7            Summary


In this chapter, we covered the all-important topic of processes. You were introduced to the Actor concurrency model. Through the example application, we’ve learnt how to:


·      Create processes


·      Send and receive messages using processes


·      Concurrency can be achieved using multiple processes


·      Messages from worker processes can collected and manipulated using another coordinator process


You have just been given a taste of concurrent programming in Elixir! Have fun doing the exercises, and be sure to give your brain a little break. See you in the next chapter, where we will learn about the *secret sauce* of Elixir – OTP!





[****[1]****](#uawOqHhyhtkQ2B699h55Lj4) http://www.erlang.org/doc/man/erl.html#max\_processes




[****[2]****](#uaLcTH2WZVUhi5sgnh6hkO7) http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.116.1969&rep=rep1&type=pdf





