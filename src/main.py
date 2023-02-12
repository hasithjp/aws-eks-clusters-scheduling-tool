from h2o_wave import main, app, Q, ui
import time
from .ui_components import *
from .aws_functions import *

columns = [
    ui.table_column(name='index', label='Index', searchable=True, cell_overflow='tooltip', data_type='number', max_width='40'),
    ui.table_column(name='cluster', label='Cluster Name', sortable=True, searchable=True, cell_overflow='tooltip', max_width='200'),
    ui.table_column(name='region', label='Region', sortable=True, searchable=True, cell_overflow='tooltip', max_width='100'),
    ui.table_column(name='nodegroups', label='Node Groups', sortable=True, searchable=True, cell_overflow='wrap', max_width='280'),
    ui.table_column(name='desired', label='Desired Size', sortable=True, searchable=True, cell_overflow='tooltip', max_width='100'),
    ui.table_column(name='min', label='Min Size', sortable=True, searchable=True, cell_overflow='tooltip', max_width='100'),
    ui.table_column(name='max', label='Max Size', sortable=True, searchable=True, cell_overflow='tooltip', max_width='100'),
    ui.table_column(name='state', label='State', sortable=True, filterable=True, min_width='130px',
                    cell_type=ui.tag_table_cell_type(
                        name='tags',
                        tags=[
                            ui.tag(label='STOPPED', color='#B03A2E'),
                            ui.tag(label='RUNNING', color='#239B56')
                            ]
                        )
                    ),
    ui.table_column(name='schedule', label='Scheduled Actions', sortable=True, filterable=True, min_width='250px',
                    cell_type=ui.tag_table_cell_type(
                        name='tags',
                        tags=[
                            ui.tag(label='STOP-ON-WEEKENDS', color='#1F618D'),
                            ui.tag(label='OTHER', color='#B7950B'),
                            ui.tag(label='N/A', color='#283747')
                        ]
                    )
                    ),
    ui.table_column(name='timezone', label='Weekend Schedule TZ', sortable=True, searchable=True, cell_overflow='tooltip', max_width='210')
]


# Main Function
@app('/')
async def serve(q: Q):
    try:
        # Handle submit button click at the startup      
        if q.args.submit:
            main_layout(q)
            q.client.project = str(q.args.project_menu)
            q.client.selected_region = str(q.args.selected_region)
            q.client.rows = process_table_rows(q.client.project, q.client.selected_region)
            generate_eks_table(q, columns, q.client.rows, q.client.project, q.client.selected_region)
        
        # Handle refresh table button    
        elif q.args.refresh_table:
            q.client.project = str(q.args.selected_project_secondary)
            q.client.selected_region = str(q.args.selected_region_secondary)
            q.client.rows = process_table_rows(q.client.project, q.client.selected_region)
            generate_eks_table(q, columns, q.client.rows, q.client.project, q.client.selected_region)

        # Handle row click and generate side panel
        elif q.args.eks_clusters:
            q.client.row_id = int(q.args.eks_clusters[0])
            cluster_name = q.client.rows[q.client.row_id-1].cells[1]
            region = q.client.rows[q.client.row_id-1].cells[2]
            cluster_state = q.client.rows[q.client.row_id-1].cells[7]
            nodegroups = q.client.rows[q.client.row_id-1].cells[3]
            nodegroups = nodegroups.strip('[')
            nodegroups = nodegroups.strip(']')
            nodegroups = nodegroups.replace("'", "")
            nodegroups = nodegroups.split(', ')

            if cluster_state == 'RUNNING':
                side_panel_text = 'Stop the Cluster?'
                side_panel_button1 = 'stop_eks'
            else:
                side_panel_text = 'Start the Cluster?'
                side_panel_button1 = 'start_eks'

            title = f"EKS Cluster: {cluster_name}"
            aws_url = get_cluster_aws_link(cluster_name, q.client.rows[q.client.row_id-1].cells[2])
            if 'STOP-ON-WEEKENDS' in q.client.rows[q.client.row_id-1].cells[8]:
                stop_on_wk_state = True
                dropdown_disabled = True
            else:
                stop_on_wk_state = False
                dropdown_disabled = False
            
            tot_cluster_cost_info = calc_approx_weekend_savings(cluster_name, region, nodegroups, cluster_state)
            generate_side_panel(q, title, side_panel_text, side_panel_button1, stop_on_wk_state, dropdown_disabled, aws_url, tot_cluster_cost_info)

        # Handle side panel YES button click
        elif q.args.stop_eks or q.args.start_eks:
            q.page['meta'].side_panel.items[4].button.disabled = True
            q.page['meta'].side_panel.items[17].button.disabled = True
            q.page['meta'].side_panel.items[0].progress.visible = True
            await q.page.save()
            cluster_name = q.client.rows[q.client.row_id-1].cells[1]
            region = q.client.rows[q.client.row_id-1].cells[2]
            nodegroups = q.client.rows[q.client.row_id-1].cells[3]
            nodegroups = nodegroups.strip('[')
            nodegroups = nodegroups.strip(']')
            nodegroups = nodegroups.replace("'", "")
            nodegroups = nodegroups.split(', ')

            if q.args.stop_eks:
                print('[INFO] STOPPING EKS:', cluster_name)
                scale_cluster(cluster_name, region, nodegroups, 'stop_eks')
                q.client.rows[q.client.row_id-1].cells[7] = 'STOPPED'
                q.client.rows[q.client.row_id-1].cells[4] = '[0]'
                q.client.rows[q.client.row_id-1].cells[5] = '[0]'
                print('[INFO] STOPPED EKS:', cluster_name)
            else:
                print('[INFO] STARTING EKS', cluster_name)
                desired_size = scale_cluster(cluster_name, region, nodegroups, 'start_eks')
                q.client.rows[q.client.row_id-1].cells[7] = 'RUNNING'
                q.client.rows[q.client.row_id-1].cells[4] = f"[{desired_size}]"
                print('[INFO] STARTED EKS', cluster_name)
            
            # Update table without processing aws data
            q.page['meta'].side_panel = None
            generate_eks_table(q, columns, q.client.rows, q.client.project, q.client.selected_region)
            await q.page.save()

        # Handle side panel scheduled actions submit button click
        elif q.args.side_panel_submit:
            q.page['meta'].side_panel.items[4].button.disabled = True
            q.page['meta'].side_panel.items[17].button.disabled = True
            q.page['meta'].side_panel.items[0].progress.visible = True
            await q.page.save()
            cluster_name = q.client.rows[q.client.row_id-1].cells[1]
            region = q.client.rows[q.client.row_id-1].cells[2]
            schedule = q.client.rows[q.client.row_id-1].cells[8]
            nodegroups = q.client.rows[q.client.row_id-1].cells[3]
            nodegroups = nodegroups.strip('[')
            nodegroups = nodegroups.strip(']')
            nodegroups = nodegroups.replace("'", "")
            nodegroups = nodegroups.split(', ')

            # Set `stop on weekend` schedule
            if q.args.stop_on_weekends_toggle:
                print('[INFO] ADD WEEKEND SCHEDULED ACTION ON', cluster_name)
                timezone = str(q.args.timezone_menu)
                state = q.client.rows[q.client.row_id-1].cells[7]
                set_scheduled_actions_on_cluster(cluster_name, region, nodegroups, timezone, state)
                time.sleep(5)
                print('[INFO] ADDED WEEKEND SCHEDULED ACTION ON', cluster_name)
                if schedule == 'OTHER':
                    q.client.rows[q.client.row_id-1].cells[8] = 'STOP-ON-WEEKENDS,OTHER'
                    q.client.rows[q.client.row_id-1].cells[9] = timezone
                elif schedule == 'N/A':
                    q.client.rows[q.client.row_id-1].cells[8] = 'STOP-ON-WEEKENDS'
                    q.client.rows[q.client.row_id-1].cells[9] = timezone
                else:
                    pass

            else:  # Remove `stop on weekend` schedule
                print('[INFO] REMOVE WEEKEND SCHEDULED ACTION ON', cluster_name)
                delete_schedule_actions_cluster(cluster_name, region, nodegroups)
                time.sleep(5)
                print('[INFO] REMOVED WEEKEND SCHEDULED ACTION ON', cluster_name)
                if schedule == 'STOP-ON-WEEKENDS,OTHER':
                    q.client.rows[q.client.row_id-1].cells[8] = 'OTHER'
                    q.client.rows[q.client.row_id-1].cells[9] = '-'
                elif schedule == 'STOP-ON-WEEKENDS':
                    q.client.rows[q.client.row_id-1].cells[8] = 'N/A'
                    q.client.rows[q.client.row_id-1].cells[9] = '-'
                else:
                    pass

            # Update table
            q.page['meta'].side_panel = None
            generate_eks_table(q, columns, q.client.rows, q.client.project, q.client.selected_region)
            await q.page.save()

        # Handle side panel CLOSE button click
        elif q.events.eks_side_panel:
            if q.events.eks_side_panel.dismissed:
                q.page['meta'].side_panel = None

        # App startup
        else:
            startup_window(q)

    except Exception as error:      
        print("[ERROR]", error)
        q.page['meta'] = ui.meta_card(box='', notification_bar=ui.notification_bar(
            text=str(error),
            type='error',
            position='top-right',
        ))

    await q.page.save()
