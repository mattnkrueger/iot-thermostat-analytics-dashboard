import dash_mantine_components as dmc

def build_footer_col(label: str, links: dict):
    label_component = dmc.Text(
        children=label,
        size="lg",
        fw="700"
    )

    nested = [
        dmc.Anchor(
            href=val,
            target="_blank",
            children=key,
            size="sm"
        )
        for key, val in links.items()
    ]

    return dmc.Stack(
        [
            label_component,
            dmc.Stack(
                nested,
                gap="sm" 
            )
        ],
        justify="start",
        align="start",
        mx="sm"
    )


# LINKEDIN_LINKS = {
#     "Steven Austin": "./404",
#     "Sage Marks": "https://www.linkedin.com/in/sage-marks/",
#     "Matt Krueger": "https://www.linkedin.com/in/mattnkrueger/",
#     "Zack Mulholland": "https://www.linkedin.com/in/zack-mulholland-317914254/",
# }

DOCUMENTATION_LINKS = {
    "Source Code": "https://github.com/Senior-Design-2025-2026/ECE-Senior-Design-Lab-1-EXTENSION",
    "Requirements": "https://github.com/Senior-Design-2025-2026/ECE-Senior-Design-Lab-1-EXTENSION/blob/main/img/lab-1.pdf",
    "Lab Report": "https://github.com/Senior-Design-2025-2026/ECE-Senior-Design-Lab-1-EXTENSION/blob/main/img/lab-report.pdf",
    "Team GitHub": "https://github.com/Senior-Design-2025-2026"
}

# OTHER_PROJECTS_LINKS = {
#     "Lab 1 (THIS!)": "https://github.com/Senior-Design-2025-2026",
#     "Lab 2 (TBD)": "./404",
#     "Lab 3 (TBD)": "./404",
#     "Final (TBD)": "./404",
# }

documentation_col = build_footer_col("Documentation", DOCUMENTATION_LINKS)
# linked_in_col = build_footer_col("Team Members", LINKEDIN_LINKS)
# other_projects = build_footer_col("Our Projects", OTHER_PROJECTS_LINKS)

university_statement = dmc.Card(
    dmc.Stack(
        [
            dmc.Stack(
                [
                    dmc.Text(
                        children="Team 3",
                        size="30px",
                        fw="900"
                    ),
                    dmc.Badge(
                        "ECE Senior Design • Lab 1",
                    ),
                ],
                gap="sm"
            ),
            dmc.Text(
                children="""
                Principles of ECE/CSE Design Fall 2025.
                University of Iowa, College of Engineering. 
                """,
                size="sm",
                fs="italic",
                maw="200px"
            ),
        ],
    )
)

def footer():
    external_links = dmc.Box(
            dmc.Group(
            [
                university_statement,
                documentation_col,
                # linked_in_col,
                # other_projects,
            ], 
            justify="space-evenly",
            align="start",
            wrap="wrap",
            py="md"
        ),
        style={
            "border-top":"1px solid var(--app-shell-border-color)",
        }
    )

    return external_links
