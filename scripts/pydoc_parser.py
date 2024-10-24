import ast
import os
import markdown as m

# Define the fields you want to extract from the pydoc
PYDOC_FIELDS = [
    "Name",
    "Job Title",
    "Job Purpose",
    "Required Resources",
    "S3 Bucket Dependencies",
    "Execution Schedule",
    "Scheduler",
    "Job Priority",
    "Expected Impact",
    "Step Function Used",
    "Lambda Function Used",
    "Notification Channels",
    "Email Subject",
    "Output Format",
    "Output S3 Bucket"
]


def extract_pydocs_from_file(file_path):
    with open(file_path, "r") as file:
        file_content = file.read()

    # Parse the file content into an AST
    tree = ast.parse(file_content)

    pydocs = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Module):
            # Check if there is a docstring for the module
            if ast.get_docstring(node):
                docstring = ast.get_docstring(node)
                # Split the docstring into lines
                docstring_lines = docstring.split('\n')
                pydoc_info = {
                    'name': '',
                    'docstring': docstring,
                    'fields': {}
                }
                # Extract pydoc fields from the docstring
                for line in docstring_lines:
                    # Example logic to extract fields
                    for field in PYDOC_FIELDS:
                        if line.startswith(field):
                            # Capture the field's value
                            pydoc_info['fields'][field] = line.split(':', 1)[1].strip()
                            # If 'Name' is found, set it as the name
                            if field == "Name":
                                pydoc_info['name'] = pydoc_info['fields'][field]
                            break  # Break after finding a field
                    # If 'Name' wasn't explicitly found, fallback to a generic name
                if not pydoc_info['name']:
                    pydoc_info['name'] = os.path.basename(file_path)  # Use the filename as a fallback

                pydoc_info['name'] = pydoc_info['name'].split('.')[0]
                pydocs.append(pydoc_info)

    return pydocs


def parse_pydoc(pydoc):
    """Parse the pydoc string to extract fields and format them."""
    doc_dict = {}
    current_field = None
    for line in pydoc.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Check if the line starts with any of the predefined fields
        for field in PYDOC_FIELDS:
            if line.startswith(field):
                current_field = field
                doc_dict[current_field] = line[len(field):].strip()
                break
        else:
            # Append additional content to the current field
            if current_field:
                doc_dict[current_field] += ' ' + line.strip()

    # Ensure all fields are present in the doc, even if empty
    for field in PYDOC_FIELDS:
        if field not in doc_dict:
            doc_dict[field] = "Not provided"

    return doc_dict


def generate_markdown(pydoc_info, file_name):
    """Generate Markdown documentation from pydoc information."""
    markdown_content = f"# Documentation for {file_name}\n\n"
    markdown_content += "\n\n"

    job_count = 1
    for doc in pydoc_info:
        markdown_content += f"## {job_count}. {doc['name']}\n"
        for field, content in doc['fields'].items():
            markdown_content += f"### {field}:\n"
            markdown_content += f"{content}\n\n"

        markdown_content += "====================================\n\n\n\n\n"
        job_count += 1

    return markdown_content


def parse_directory(directory):
    """Parse all Python files in a given directory."""
    all_pydoc_info = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                pydoc_info = extract_pydocs_from_file(file_path)
                all_pydoc_info.extend(pydoc_info)

    return all_pydoc_info


def get_repo_name(directory):
    # Get the absolute path
    abs_path = os.path.abspath(directory)
    # Split the path into components
    path_components = abs_path.split(os.sep)
    # The repository name will be the last non-empty component
    repo_name = next((component for component in reversed(path_components) if component), None)
    return repo_name


def main(directory, output_md):
    repo_name = get_repo_name(directory)
    print(f"Repository name: {repo_name}")

    all_pydoc_info = parse_directory(directory)

    # Create the output directory if it doesn't exist
    output_dir = os.path.dirname(output_md)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if all_pydoc_info:
        markdown = generate_markdown(all_pydoc_info, repo_name)
        with open(output_md, 'w', encoding='utf-8') as md_file:
            md_file.write(markdown)

        # Convert the markdown content to HTML
        html_content = m.markdown(markdown)

        with open('docs/pydoc.html', 'w', encoding='utf-8') as md_file:
            md_file.write(html_content)

        print(f"Documentation generated: {output_md}")


    else:
        print("No pydocs found.")


if __name__ == "__main__":
    main('.', 'docs/pydoc.md')
