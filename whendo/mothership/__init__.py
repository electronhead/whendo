"""
That these modules are imported here ensures that Action and Scheduler resolution will use their entire
inheritance trees to derive an instance from a dictionary.

The imports were not instead included in mothership.actions.__init__.py in order to make sure that
the inheritance trees are available before the function util.resolve_instance(...) is called.

And thus was Equus again slain.
"""
import mothership.util
import mothership.action
import mothership.scheduler
import mothership.actions.file_action
import mothership.actions.gpio_action
import mothership.actions.http_action