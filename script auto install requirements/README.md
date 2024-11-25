

This script is designed to automate the setup of essential tools, packages, and configurations for a development environment. It is specifically tailored for Ubuntu and includes functionalities like updating the system, installing Node.js, Docker, Docker Compose, and other dependencies.

Features

	•	System Update: Automatically updates and upgrades the system packages.
	•	Essential Tools Installation: Installs essential tools like curl, wget, screen, and jq.
	•	Custom Scripts Execution: Downloads and runs additional setup scripts from a GitHub repository.
	•	Node.js and NVM Installation: Installs Node.js via NVM if not already present.
	•	Docker Installation: Ensures Docker is installed and configured correctly.
	•	Docker Compose Installation: Fetches and installs the latest version of Docker Compose.
	•	Retry Mechanism: Retries package installation up to three times if it fails.
	•	Color-coded Logging: Provides visually appealing messages for success, warnings, and errors.
	•	Silent Mode: Includes a silent mode for unattended installations.

Prerequisites

	•	Operating System: Ubuntu (Tested on Ubuntu 20.04 and above)
	•	User Privileges: Root or a user with sudo privileges.

Usage

	1.	Clone the repository or copy the script to your local machine:

wget -O install.sh https://your-repo-url/install.sh
chmod +x install.sh


	2.	Run the script:

./install.sh


	3.	To enable silent mode (auto-confirmation for installations):

./install.sh -s



Script Highlights

	•	Verification of OS: Ensures the script is only run on Ubuntu.
	•	Retry Mechanism: Retries critical installations up to three times in case of failure.
	•	Silent Mode: Pass -s to suppress user prompts for unattended setups.
	•	Automatic Docker Group Addition: Adds the current user to the docker group.

Logs

	•	All logs are saved to install_log.txt for debugging or audit purposes.

Outputs

After successful execution, the script provides:
	•	Node.js version
	•	npm version
	•	Docker version
	•	Docker Compose version

Customization

	•	Modify the retry_install function to add additional packages.
	•	Adjust the URLs to your custom repositories if necessary.

Troubleshooting

	•	If you encounter issues, check install_log.txt for detailed logs.
	•	Ensure the script has execute permissions:

chmod +x install.sh


	•	Make sure your user has sudo privileges to install packages and modify system configurations.

Additional Notes

	•	Ensure you log out and log back in after Docker installation to apply the docker group changes.
	•	Visit the GitHub repository for updates and more tutorials: GitHub Repository.

License

This script is distributed under the MIT License. Feel free to use, modify, and distribute it.