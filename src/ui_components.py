# ui_components.py>
from .layouts import *


def generate_side_panel(q: Q, title, side_panel_text, side_panel_button1, stop_on_wk_state, dropdown_disabled, aws_url, tot_cluster_cost_info):
    tot_ec2s = str(tot_cluster_cost_info[3])
    ec2_types = str(tot_cluster_cost_info[0])
    ec2_costs = str(tot_cluster_cost_info[1])
    tot_daily_cost = str("{:.5f}".format(tot_cluster_cost_info[2]))
    weekend_savings = str("{:.5f}".format(tot_cluster_cost_info[2]*2))
    q.page['meta'].side_panel = ui.side_panel(
        name='eks_side_panel',
        title=title,
        closable=True,
        blocking=True,
        events=['dismissed'],
        items=[
            ui.progress(label='', caption='Waiting...', visible=False),
            ui.link(label='Go to AWS Console', path=aws_url, target='_blank'),
            ui.separator(),
            ui.text_l(side_panel_text),
            ui.button(name=side_panel_button1, label='Yes', primary=True),
            ui.separator(),
            ui.text_xl('Cost Details'),
            ui.text(f"Total Instances: {tot_ec2s}"),
            ui.text(f"Instances Types: {ec2_types}"),
            ui.text(f"Instances Cost/Hr($): {ec2_costs}"),
            ui.text(f"Total Daily Cost (Approx.): ${tot_daily_cost}"),
            ui.text_l(f"Approx. Cost Savings By Stopping On Weekend: ${weekend_savings}"),
            ui.separator(),
            ui.text_xl('Scheduled Actions'),
            ui.text('Stop On Weekends: Scale down cluster size to 0 on 12AM Sat & Scale Up Cluster Size Past desired size on 12AM Mon based on the given TZ'),
            ui.toggle(name='stop_on_weekends_toggle', label='Stop On Weekends', value=stop_on_wk_state),
            ui.dropdown(name='timezone_menu', label='Time Zone', value='Etc/UTC', required=True, disabled=dropdown_disabled, choices=[
                ui.choice(name='Etc/UTC', label='Etc/UTC'),
                ui.choice(name='US/Pacific', label='US/Pacific'),
                ui.choice(name='Asia/Colombo', label='Asia/Colombo'),
                ui.choice(name='Asia/Singapore', label='Asia/Singapore'),
                ui.choice(name='Canada/Eastern', label='Canada/Eastern'),
                ui.choice(name='Europe/Prague', label='Europe/Prague'),
                ui.choice(name='Europe/Warsaw', label='Europe/Warsaw'),
                ui.choice(name='Asia/Jerusalem', label='Asia/Jerusalem'),
                ui.choice(name='PST8PDT', label='PST8PDT'),
                ui.choice(name='CET', label='CET'),
                ui.choice(name='CST6CDT', label='CST6CDT'),
                ui.choice(name='EST5EDT', label='EST5EDT'),
            ]),
            ui.button(name='side_panel_submit', label='Submit'),
            ui.separator(),

        ])


def generate_eks_table(q: Q, tab_columns, tab_rows, project, selected_region):
    q.page['main_content'] = ui.form_card(box='main_content', items=[
        ui.inline(justify='start', items=[
            ui.text_xl("Project: "),
            ui.dropdown(name='selected_project_secondary', value=project, width='140px', tooltip='Choose Project Tag and Click Refresh ', choices=[
                ui.choice(name='_PROJECT1_', label='_PROJECT1_'),
                ui.choice(name='_PROJECT2_', label='_PROJECT2_'),
                ui.choice(name='_PROJECT3_', label='_PROJECT3_'),
                ui.choice(name='All', label='All'),
            ]),
            ui.dropdown(name='selected_region_secondary', value=selected_region, width='220px', tooltip='Choose Region and Click Refresh', choices=[
                ui.choice(name='All', label='All Regions'),
                ui.choice(name='us-east-1', label='us-east-1 N.Virginia'),
                ui.choice(name='us-east-2', label='us-east-2 Ohio'),
                ui.choice(name='us-west-1', label='us-west-1 N.California'),
                ui.choice(name='us-west-2', label='us-west-2 Oregon'),
                ui.choice(name='ap-south-1', label='ap-south-1 Mumbai'),
                ui.choice(name='ap-southeast-1', label='ap-southeast-1 Singapore'),
                ui.choice(name='eu-central-1', label='eu-central-1 Frankfurt')
            ]),
            ui.button(name='refresh_table', icon='Refresh', tooltip='Refresh Table after choosing Project and Region')

        ]),
        ui.separator(),
        ui.table(
            name='eks_clusters',
            columns=tab_columns,
            rows=tab_rows,
            groupable=True,
            downloadable=True,
            resettable=False,
            height='900px'
        ),
    ])


def startup_window(q: Q):
    startup_layout(q)
    q.page['submission'] = ui.form_card(
        box='submission',
        items=[
            ui.separator(),
            ui.text_xl(" "), ui.text_xl(" "),
            ui.inline(justify='center', items=[
                ui.dropdown(name='project_menu', label='Project?', value='All', width='350px', required=True, choices=[
                    ui.choice(name='_PROJECT1_', label='_PROJECT1_'),
                    ui.choice(name='_PROJECT2_', label='_PROJECT2_'),
                    ui.choice(name='_PROJECT3_', label='_PROJECT3_'),
                    ui.choice(name='All', label='All'),
                ]),
            ]),
            ui.inline(justify='center', items=[
                ui.dropdown(name='selected_region', label='Region?', value='All', width='350px', choices=[
                    ui.choice(name='All', label='All'),
                    ui.choice(name='us-east-1', label='us-east-1/N.Virginia'),
                    ui.choice(name='us-east-2', label='us-east-2/Ohio'),
                    ui.choice(name='us-west-1', label='us-west-1/N.California'),
                    ui.choice(name='us-west-2', label='us-west-2/Oregon'),
                    ui.choice(name='ap-south-1', label='ap-south-1/Mumbai'),
                    ui.choice(name='ap-southeast-1', label='ap-southeast-1/Singapore'),
                    ui.choice(name='eu-central-1', label='eu-central-1/Frankfurt')
                ]),
            ]),
            ui.text_xl(" "), ui.text_xl(" "),
            ui.inline(justify='center', items=[
                ui.button(name='submit', label='Proceed', primary=True)
            ]),
            ui.text_xl(" "), ui.text_xl(" "), ui.text_xl(" "),
            ui.separator(),

        ]
    )
