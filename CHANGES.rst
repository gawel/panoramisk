1.1 (2016-12-29)
----------------

- We no longer loosing calls on reconnection

- End of support for python<3.4

- Better test coverage

1.0 (2015-08-19)
----------------

- Add FastAGI server, implemented with high-level AsyncIO API (Streams)
- Add events parameter for Manager, to disable AMI events reception (Useful for performance reasons)
- Finish AsyncAGI commands support (WIP)

0.6 (2014-11-16)
----------------

- Avoid failure when factory is not already set

0.5 (2014-11-16)
----------------

- AMI command results tracking fixed
- Return AMI command result with multiple events in a Future
- Return AsyncAGI command result in a Future
- Add several examples
- Internal refactoring
- Remove arawman support
- Remove external dependencies
- Add support for multiple responses from Actions (example: QueueStatus)
- Improved performance with Events pattern matching
- Add mocked test wrapper
- Add coroutine support for Events dispatching
- Invert event callback signature to create Manager methods to handle events
- Support of AMI commands
- Support of AsyncAGI commands (Not finished)

0.4 (2014-05-30)
----------------

- Compat with the latest trollius


0.3 (2014-01-10)
----------------

- Don't send commands twice


0.2 (2014-01-09)
----------------

- Initial release
