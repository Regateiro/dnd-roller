# D&D Roller

Available Commands (can be shorthanded to the first letter):

```
!roll <dice>                                                   # Roll the dice using dice notation
!roll [<character>] <skill|macro> [crit] [save] [a|ta|d] [var] # Roll a character's stat, save or skill check

!distance <ground> <vertical> <diagonal>                       # Calculates distances (use 0 to indicate the one to calculate)

!f <height>                                                    # Calculates how long to hit the ground while free-falling

!character                                                     # Manage user characters
  - list                                                       # List all your characters
  - active [<character>]                                       # Sets the active character (shows the current one if omitted)
  - info [<character>]                                         # Shows a character information
  - show [<character>]                                         # Alias for info (see info)
  - create <character> <full_template>                         # Create/Overwrite a character
  - update <character> main <main_template>                    # Update the character's main stats
  - update <character> saves <saves_template>                  # Update the character's save proficiencies
  - update <character> skills <skills_template>                # Update the character's skill proficiencies
  - update <character> expertise <expertise_template>          # Update the character's skill expertise
  - delete <character>                                         # Delete a character
  - help                                                       # Show more detailed help
```

Advanced Commands (can be shorthanded to the first letter):

```
!macro                                          # Manage character macros
  - set [<character>] <name> <dice>             # Set a macro using dice notation for a character
  - delete [<character>] <name>                 # Delete a macro from a character
  - list [<character>]                          # List all the macros for a character
  - help                                        # Show more detailed help

!variable                                       # Manage character variables to use as modifiers
  - set [<character>] <name> <value>            # Set a variable value for a character
  - delete [<character>] <name>                 # Delete a variable from a character
  - list [<character>]                          # List all the variables for a character
  - help                                        # Show more detailed help
```

Available Session Management Commands (can be shorthanded to the first letter):

```
!session                          # Manage server's sessions.
  - weekday <monday|tuesday|...>  # Sets the default weekday for sessions.
  - list                          # List all the currently scheduled sessions and player unavailabilities.
  - next                          # List the next scheduled session and player unavailabilities.
  - schedule <YYYY-MM-DD>         # Schedule a session for the given date.
  - cancel  <YYYY-MM-DD>          # Cancel a session scheduled for the given date.
  - available  <YYYY-MM-DD>       # Set a player as available for a given session. This is the default setting.
  - unavailable <YYYY-MM-DD>      # Set a player as unavailable for a given session.
  - help                          # Show this help.
```
