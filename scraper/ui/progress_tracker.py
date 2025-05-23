from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from datetime import datetime
from typing import Optional

from models.data_models import ProcessingStats

class ProgressTracker:
    """Handles UI display and progress tracking for the pipeline"""
    
    def __init__(self):
        self.console = Console()
        self.stats = ProcessingStats()
    
    def create_summary_table(self) -> Table:
        """Create a table summarizing current progress"""
        table = Table(show_header=True, box=box.ROUNDED)
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        elapsed = "calculating..." if not self.stats.start_time else str(datetime.now() - self.stats.start_time).split('.')[0]
        
        table.add_row("Pipeline Started", self.stats.start_time.strftime("%H:%M:%S") if self.stats.start_time else "Not started")
        table.add_row("Elapsed Time", elapsed)
        table.add_row("Companies Processed", f"{self.stats.processed_companies}/{self.stats.total_companies}")
        table.add_row("Companies with Devices", str(self.stats.companies_with_devices))
        table.add_row("Companies without Devices", str(self.stats.companies_without_devices))
        table.add_row("Companies with Contacts", str(self.stats.companies_with_contacts))
        table.add_row("Companies without Contacts", str(self.stats.companies_without_contacts))
        table.add_row("Total Devices Found", str(self.stats.total_devices))
        table.add_row("Devices Processed", str(self.stats.processed_devices))
        table.add_row("Total Contacts Found", str(self.stats.total_contacts))
        table.add_row("Contacts Processed", str(self.stats.processed_contacts))
        table.add_row("Total Certificates Found", str(self.stats.total_certificates))
        table.add_row("Certificates Processed", str(self.stats.processed_certificates))
        
        if self.stats.processed_companies > 0:
            avg_devices = self.stats.total_devices / self.stats.processed_companies
            table.add_row("Average Devices per Company", f"{avg_devices:.2f}")
            
            avg_contacts = self.stats.total_contacts / self.stats.processed_companies
            table.add_row("Average Contacts per Company", f"{avg_contacts:.2f}")
        
        if self.stats.processed_certificates > 0:
            avg_certificates = self.stats.total_certificates / self.stats.processed_companies if self.stats.processed_companies > 0 else 0
            table.add_row("Average Certificates Found", f"{avg_certificates:.2f}")
        
        return table
    
    def display_status_update(self, message: str, style: str = "bold white") -> None:
        """Display a status update with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[grey]{timestamp}[/grey] [green]•[/green] {Text(message, style=style)}")
    
    def display_pipeline_title(self, iso_code: str, max_companies: Optional[int] = None, 
                             max_devices: Optional[int] = None, pipeline_type: str = "Complete") -> None:
        """Display the main pipeline title panel"""
        content = f"[bold yellow]Country:[/bold yellow] {iso_code}\n"
        
        if max_companies is not None:
            content += f"[bold yellow]Max Companies:[/bold yellow] {max_companies}\n"
        
        if max_devices is not None:
            content += f"[bold yellow]Max Devices per Company:[/bold yellow] {max_devices}\n"
        
        content += f"[bold yellow]Limit:[/bold yellow] {max_companies if max_companies is not None else 'All (no limit)'}"
        
        title_panel = Panel(
            content,
            title=f"[bold]EUDAMED {pipeline_type} Pipeline[/bold]",
            subtitle="[italic]Processing companies one by one[/italic]",
            border_style="cyan",
        )
        self.console.print(title_panel)
    
    def display_company_panel(self, company_name: str, company_uuid: str, iso_code: str) -> None:
        """Display company processing panel"""
        company_panel = Panel(
            f"[bold]{company_name}[/bold]\n[blue]UUID:[/blue] {company_uuid}\n[blue]Country:[/blue] {iso_code}",
            title="[bold cyan]Processing Company[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(company_panel)
    
    def display_progress_header(self, company_name: str, company_index: int, total_companies: int) -> None:
        """Display progress header for a company"""
        progress_header = Panel(
            f"[bold green]Company {company_index+1}/{total_companies}[/bold green]: [bold]{company_name}[/bold]",
            border_style="green"
        )
        self.console.print(progress_header)
    
    def display_devices_summary(self, company_name: str, device_count: int) -> None:
        """Display device summary for a company"""
        device_panel = Panel(
            f"Found [bold green]{device_count}[/bold green] devices for [bold]{company_name}[/bold]",
            border_style="green" if device_count > 0 else "yellow"
        )
        self.console.print(device_panel)
    
    def display_completion_summary(self, company_name: str, devices_processed: int) -> None:
        """Display company completion summary"""
        completion_panel = Panel(
            f"Company [bold]{company_name}[/bold] completed with [bold green]{devices_processed}[/bold green] devices processed",
            title="[bold green]Company Processing Complete[/bold green]",
            border_style="green"
        )
        self.console.print(completion_panel)
    
    def display_summary_panel(self, title: str, subtitle: str, border_style: str = "green") -> None:
        """Display a summary panel with the current stats"""
        summary_panel = Panel(
            self.create_summary_table(),
            title=f"[bold]{title}[/bold]",
            subtitle=subtitle,
            border_style=border_style
        )
        self.console.print(summary_panel)
    
    def display_final_summary(self, iso_code: str, companies_processed: int, 
                            total_devices: int, certificates_processed: int = 0,
                            pipeline_type: str = "Complete") -> None:
        """Display final pipeline summary"""
        elapsed_time = datetime.now() - self.stats.start_time if self.stats.start_time else "unknown"
        elapsed_str = str(elapsed_time).split('.')[0]  # Remove microseconds
        
        content = f"""[bold green]{pipeline_type} Pipeline Completed Successfully![/bold green]
        
[bold]Country:[/bold] {iso_code}
[bold]Companies Processed:[/bold] {companies_processed} / {self.stats.total_companies}
[bold]Total Devices Processed:[/bold] {total_devices}
[bold]Companies with Devices:[/bold] {self.stats.companies_with_devices}
[bold]Companies without Devices:[/bold] {self.stats.companies_without_devices}
[bold]Total Contacts Processed:[/bold] {self.stats.processed_contacts}
[bold]Companies with Contacts:[/bold] {self.stats.companies_with_contacts}
[bold]Companies without Contacts:[/bold] {self.stats.companies_without_contacts}"""
        
        if certificates_processed > 0:
            content += f"\n[bold]Certificates Processed:[/bold] {certificates_processed} / {self.stats.total_certificates}"
        
        content += f"\n[bold]Total Runtime:[/bold] {elapsed_str}"
        
        if companies_processed > 0:
            avg_time = str(elapsed_time / companies_processed).split('.')[0]
            content += f"\n\n[italic]Average processing time per company: {avg_time}[/italic]"
        
        final_summary = Panel(
            content,
            title=f"[bold]{pipeline_type} Pipeline Summary[/bold]",
            border_style="green",
            width=80
        )
        self.console.print(final_summary)
    
    def start_timer(self) -> None:
        """Start the pipeline timer"""
        self.stats.start_time = datetime.now()
    
    def update_stats(self, **kwargs) -> None:
        """Update statistics"""
        for key, value in kwargs.items():
            if hasattr(self.stats, key):
                setattr(self.stats, key, value)
    
    def increment_stats(self, **kwargs) -> None:
        """Increment statistics"""
        for key, value in kwargs.items():
            if hasattr(self.stats, key):
                current_value = getattr(self.stats, key)
                setattr(self.stats, key, current_value + value) 