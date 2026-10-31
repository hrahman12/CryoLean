# CryoLean

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/e0c64585-dddc-47d8-a132-848fa78e7c3c" />

<img width="2989" height="1815" alt="image" src="https://github.com/user-attachments/assets/178931bc-4b6c-43e0-80ed-d97f642310e1" />


CryoLean
Cryo, made simple.
A simple product proposal.

CryoLean helps you answer one question:
Can this cryostat do the experiment I have in mind?

A cryostat is equipment that keeps a sample at a controlled low temperature. CryoLean helps you compare these machines, choose a setup, and understand whether it meets your experiment’s requirements.

The experience should feel like a familiar app: choose what you want to do, choose a machine, and get a clear answer.

AI suggests a setup. Lean checks the proof that it follows the stated requirements.
What the person does
1. Choose an experiment. Pick a task from a short menu.
2. Choose a cryostat. See a large picture of the selected machine.
3. Check the setup. The app compares the experiment’s requirements with the equipment information.
4. Read the result. See whether the requirements are met, something conflicts, or information is missing.
5. Try another option. Switch cryostats or review a suggested change, then check again.
The app asks short, specific questions when it needs more information. It should help someone understand what to enter instead of presenting a long technical form.
What the screen looks like
The design is inspired by the simplicity of Apple’s interfaces: a light background, clear words, generous spacing, and a few obvious controls.
A large cryostat image
The selected cryostat is the main object on the screen. Its name appears underneath. A simple cutaway can show where the sample goes.

The picture changes when the user selects a different machine. Different types of cryostats get their own appropriate images.
“What would you like to do?”
A simple experiment picker sits beside the image. Small category tabs organize the choices:
- Biology
- Chemistry
- Materials
Experiment names should describe the task in everyday language, such as Examine a frozen sample or Test a material at low temperature.

Each choice opens a prepared experiment profile: a saved list of what that task needs. The user reviews it and supplies any missing details. The app must not guess important requirements just to finish the check.
“Change cryostat”
This control opens a small catalog of machines. Each entry shows a picture, its name, and the relevant configuration—the particular options fitted to that machine.

Users can switch between different models and manufacturers, as well as different configurations of one model.
“Check setup”
One clear button starts the check. While it runs, the app says Checking your setup…
One clear result
The answer appears underneath the button. A small See checks link opens the reasons and supporting information.
What the answers mean
What the user sees	What it means	What happens next
Requirements met	All required checks in the selected experiment profile passed.	View the checks or save the result.
Does not meet requirements	A known equipment limit conflicts with something the experiment needs.	See the conflict and review another setup.
Need more information	An important detail is missing or cannot yet be checked.	Answer a specific question or add the missing information.


Every result should explain the next step plainly. For example:
“This cryostat cannot reach the temperature your experiment requires. Choose another cryostat.”

Or:
“We need your sample’s size before we can check whether it fits.”

Missing information must stay visible. It cannot count as a successful check.
Switching cryostats
The user should be able to try the same experiment on several machines without starting over.

When they select another cryostat, the app:
- Keeps the experiment and its requirements selected.
- Replaces the central image with the new machine.
- Loads that machine’s options and equipment information.
- Clears the previous result and checks the new setup.
If more information is needed, the app asks for it. It must never leave a previous machine’s successful result attached to the new selection.

An optional Compare cryostats view shows two or three machines against the same experiment, with a separate result for each.
Where AI and Lean fit
AI is the helper
AI helps turn the user’s description into a draft setup. It can explain a problem in ordinary language and suggest another machine or a change to the configuration.

For example:
“This model does not have the connection your experiment needs. Here is another configuration to check.”

The user reviews a suggested change before accepting it. The app keeps the experiment’s requirements unchanged unless the user explicitly chooses to edit them.
Lean is the proof checker
Behind the simple screen, the app writes the requirements as precise rules. It produces a mathematical proof that a proposed setup follows those rules. Lean checks that proof before the app shows a verified result.

In everyday terms:
AI says, “Here is a setup to try.” Lean checks the proof that the setup meets the requirements.

The result depends on the equipment information and requirements provided. A verified badge appears only after a successful Lean check. Changing the setup requires a fresh check.

The See checks link explains the details through ordinary questions:
- Is it cold enough for this experiment?
- Does the sample fit?
- Does it have the equipment and connections the experiment needs?
- What information did the check use?
These are examples; each experiment has its own required checks. The main screen stays simple while the reasons remain available.
A simple example
Someone wants to test how a small material sample behaves at a low temperature.

They choose the prepared experiment and confirm its requirements. Then they select Cryostat A.

The app reports:
Does not meet requirements. This machine cannot reach the temperature this experiment needs.

They press Change cryostat and select Cryostat B. The experiment stays selected. The image changes, and the app checks the new machine’s information.

In this example, Cryostat B passes every requirement in the profile. The app reports:
Requirements met. See checks to understand why.

If a required specification were missing, the result would instead be Need more information.

The person gets a clear answer without having to read a proof or understand the machine’s internal engineering.
The first version
Start with a small catalog of documented cryostat configurations and a few prepared experiments across Biology, Chemistry, and Materials.

Build the central image, experiment picker, cryostat switcher, three result states, and See checks view. Let people save a short report containing the selected setup, result, and supporting information.

This first version checks plans. It does not operate the physical machine or guarantee that an experiment will succeed. Its promise is specific: check whether the supplied setup meets the selected requirements.
The guiding idea
One machine. One task. One clear answer.

Keep the experience simple, make switching easy, and let people inspect the reasons whenever they want.


