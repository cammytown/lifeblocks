# LifeBlocks: A Project Management System for Creative Minds

LifeBlocks is a system for managing multiple creative projects while respecting the natural rhythms of creative work. It combines structured randomization with intentional focus periods, helping you maintain progress across many projects without losing the deep engagement that meaningful work requires.

## Core Concepts

### Project Categories

Projects fall into different categories, each weighted to ensure appropriate time allocation:

**Core Creative Projects** (4x weight)
These are your primary creative works - projects you're bringing into the world:
- Games and interactive experiences
- Programming languages and frameworks
- Musical compositions
- Research projects
- Written works

**Skill Development** (2x weight)
Focused practice and learning:
- Technical skills
- Artistic techniques
- Theoretical understanding
- Experimental practice
- Tool mastery

**Infrastructure & Maintenance** (1x weight)
Work that enables everything else:
- System organization
- Tool development
- Documentation
- Planning and review
- Resource management

**Experimental** (1.5x weight)
Early-stage exploration and discovery:
- Project prototypes
- Technical investigations
- Creative experiments
- New directions

**Human Condition** (1x weight)
The fundamentals of existing as a human:
- Cooking and meals
- Space maintenance / cleaning
- Physical systems upkeep / exercise
- Basic life organization

<!-- **Play** (0.5x weight)
Activities pursued primarily for enjoyment:
- Recreational gaming
- Casual reading
- Fun-first creative experiments
- Social games and activities
- Pure enjoyment music time
- Straight chillin -->


### Activity Duration and Timing

Activities can specify their duration in two ways:
- **Fractional Blocks**: Activities can take 0.5x, 1x, 1.5x, or 2x of the base block time
- **Minimum Duration**: Activities can specify a minimum time in minutes (e.g., 20 minutes)

The system uses whichever is longer to ensure activities get the time they need while remaining flexible to different block lengths.

When a category block contains a half-length activity, the system will select another activity from the same category to fill the remaining time. This maintains focus while providing variety within the category.


### Maximum Intervals

Activities can specify a maximum interval between sessions. This ensures important recurring activities (like meals) don't go neglected for too long. When an activity's maximum interval has been exceeded, it receives higher priority in the selection process.

This provides a flexible way to handle necessary recurring activities without rigid scheduling, while ensuring they happen with appropriate frequency.

### Temporal Management

Projects can have special timing requirements:
- **Max Intervals**: Maximum time allowed between instances (e.g., no more than 4 hours between meals)
- **Completion Tracking**: Mark activities as done or unnecessary for the current period

### The Token System

Tokens provide flexibility within the structure. Earned through consistent engagement, they can be spent on:

- **Focus**: Dedicate extended time to a single project
- **Exploration**: Pursue a new direction
- **Combination**: Intentionally merge two projects
- **Recovery**: Take intentional rest periods

Earn one token per week of consistent system use, with bonus tokens for significant milestones or insights.

### Resistance Tracking

Before each work session, note your resistance level (1-5):
1. Eager to begin
2. Ready to engage
3. Ambivalent
4. Strong resistance
5. Severe aversion

This tracking reveals valuable patterns:
- Which projects generate productive resistance
- Optimal times for different types of work
- Projects that might need restructuring
- Natural energy flows throughout the day

### Session Management

Time blocks can be measured through:
- Traditional timers
- Natural work rhythms
- Music or audio cues
- Physical timekeeping tools

Choose methods that support your focus rather than disrupt it.

## Pattern Recognition

The system helps identify:
- Natural work rhythms and energy flows
- High-value project combinations
- Optimal scheduling patterns
- Projects requiring restructuring
- Productive resistance patterns

## Implementation Notes

The goal isn't perfect adherence to a system, but rather supporting natural creative rhythms while maintaining momentum across multiple projects. Use what works, modify what doesn't, and let the system evolve with your practice.

Remember: This is a tool for enhancing your creative practice, not a taskmaster. It should feel like a helpful friend who knows when to push, when to back off, and when to remind you that you probably need to eat something.

# DEPENDENCIES
- python 3.12
- pip
- tkinter

# TODO
- make BaseDialog a subclass of tk.Toplevel?
- give option to reduce length of block; maybe check it by default if resistance is high
- improve block selection algorithm so it reduces weight of blocks not just based on recent usage, but also based on the number of times they've been selected recently
- add Restart button to completion dialog

# CREDITS
- Most of the code for the software was generated with AI, including most of this README (after some prompting and wrestling)