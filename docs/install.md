# Installation

DiTTo is the Distribution Transformation Tool. It is an open source tool to convert and modify electrical distribution system models. The most common domain of electrical distribution systems is from substations to customers.

```bash
pip install ditto
```

This will install the basic version of ditto with limited dependencies. Because ditto supports conversion between many multiple formats, dependencies can be specified during installation For example:

When extending documentation, additional dependencies are required. These can be installed using the following command.

```bash
pip install ditto[docs]
```

If you're using a virtual environment, you will want to activate it first before running the `pip install` command. Virtual environments can be activated using the following commands:

On Windows:

```bash
venv\Scripts\activate
```

On macOS and Linux:

```bash
source venv/bin/activate
```

After activating the virtual environment, you can then proceed to install the package using `pip`.
Remember to replace `venv` with the name of your virtual environment if it's different.
