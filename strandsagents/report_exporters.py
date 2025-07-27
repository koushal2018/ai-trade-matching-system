"""
Report Export Utilities for Enhanced Reconciliation Reports

This module provides export functionality for different report formats including
JSON, CSV, PDF, and Excel with proper formatting and visualization support.
"""

import json
import csv
import io
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import base64

logger = logging.getLogger(__name__)


class JSONExporter:
    """Export reports to JSON format with proper formatting"""
    
    def __init__(self):
        self.indent = 2
        self.ensure_ascii = False
    
    def export(self, report_data: Dict[str, Any], output_path: Optional[str] = None) -> Union[str, bytes]:
        """
        Export report to JSON format.
        
        Args:
            report_data: Report data dictionary
            output_path: Optional file path to save to
            
        Returns:
            JSON string or bytes if saved to file
        """
        try:
            # Convert any non-serializable objects
            serializable_data = self._make_serializable(report_data)
            
            json_content = json.dumps(
                serializable_data, 
                indent=self.indent, 
                ensure_ascii=self.ensure_ascii,
                default=str
            )
            
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(json_content)
                logger.info(f"JSON report exported to {output_path}")
                return json_content.encode('utf-8')
            
            return json_content
            
        except Exception as e:
            logger.error(f"Failed to export JSON report: {e}")
            raise
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convert object to JSON-serializable format"""
        if isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self._make_serializable(obj.__dict__)
        elif isinstance(obj, (datetime,)):
            return obj.isoformat()
        else:
            return obj


class CSVExporter:
    """Export reports to CSV format with multiple sheets for complex data"""
    
    def __init__(self):
        self.delimiter = ','
        self.quotechar = '"'
        self.encoding = 'utf-8'
    
    def export(self, report_data: Dict[str, Any], output_path: Optional[str] = None) -> Union[str, bytes]:
        """
        Export report to CSV format.
        
        Args:
            report_data: Report data dictionary
            output_path: Optional file path to save to
            
        Returns:
            CSV string or bytes if saved to file
        """
        try:
            # Generate multiple CSV sections
            csv_sections = self._generate_csv_sections(report_data)
            
            # Combine sections into single CSV
            csv_content = self._combine_csv_sections(csv_sections)
            
            if output_path:
                with open(output_path, 'w', newline='', encoding=self.encoding) as f:
                    f.write(csv_content)
                logger.info(f"CSV report exported to {output_path}")
                return csv_content.encode(self.encoding)
            
            return csv_content
            
        except Exception as e:
            logger.error(f"Failed to export CSV report: {e}")
            raise
    
    def _generate_csv_sections(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate different CSV sections for report components"""
        sections = {}
        
        # Summary section
        sections['summary'] = self._create_summary_csv(report_data.get('processing_summary', {}))
        
        # Detailed results section
        sections['detailed_results'] = self._create_detailed_results_csv(report_data.get('detailed_results', []))
        
        # AI insights section
        if report_data.get('ai_insights'):
            sections['ai_insights'] = self._create_ai_insights_csv(report_data['ai_insights'])
        
        # Performance metrics section
        sections['performance'] = self._create_performance_csv(report_data.get('performance_metrics', {}))
        
        # Recommendations section
        sections['recommendations'] = self._create_recommendations_csv(report_data.get('recommendations', []))
        
        return sections
    
    def _create_summary_csv(self, summary_data: Dict[str, Any]) -> str:
        """Create CSV for processing summary"""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter, quotechar=self.quotechar)
        
        writer.writerow(['PROCESSING SUMMARY'])
        writer.writerow(['Metric', 'Value'])
        
        for key, value in summary_data.items():
            if isinstance(value, dict):
                writer.writerow([key.replace('_', ' ').title(), ''])
                for sub_key, sub_value in value.items():
                    writer.writerow([f"  {sub_key.replace('_', ' ').title()}", str(sub_value)])
            else:
                writer.writerow([key.replace('_', ' ').title(), str(value)])
        
        writer.writerow([])  # Empty row separator
        return output.getvalue()
    
    def _create_detailed_results_csv(self, results: List[Dict[str, Any]]) -> str:
        """Create CSV for detailed reconciliation results"""
        if not results:
            return "No detailed results available\n\n"
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter, quotechar=self.quotechar)
        
        writer.writerow(['DETAILED RECONCILIATION RESULTS'])
        
        # Extract all possible field names for headers
        all_fields = set()
        for result in results:
            all_fields.update(result.keys())
            if 'field_results' in result:
                for field_name in result['field_results'].keys():
                    all_fields.add(f"field_{field_name}_status")
                    all_fields.add(f"field_{field_name}_confidence")
        
        # Create headers
        base_headers = ['trade_pair_id', 'overall_status', 'match_confidence', 'method_used', 'user_friendly_explanation']
        field_headers = sorted([f for f in all_fields if f.startswith('field_')])
        headers = base_headers + field_headers
        
        writer.writerow(headers)
        
        # Write data rows
        for result in results:
            row = []
            for header in headers:
                if header == 'trade_pair_id':
                    row.append(result.get('trade_pair_id', ''))
                elif header == 'overall_status':
                    row.append(result.get('overall_status', ''))
                elif header == 'match_confidence':
                    row.append(result.get('ai_explanation', {}).get('confidence_score', ''))
                elif header == 'method_used':
                    row.append(result.get('ai_explanation', {}).get('method_used', ''))
                elif header == 'user_friendly_explanation':
                    row.append(result.get('user_friendly_explanation', ''))
                elif header.startswith('field_'):
                    # Extract field information
                    field_name = header.replace('field_', '').replace('_status', '').replace('_confidence', '')
                    field_results = result.get('field_results', {})
                    field_result = field_results.get(field_name, {})
                    
                    if header.endswith('_status'):
                        row.append(field_result.get('status', '') if isinstance(field_result, dict) else '')
                    elif header.endswith('_confidence'):
                        row.append(field_result.get('confidence', '') if isinstance(field_result, dict) else '')
                    else:
                        row.append('')
                else:
                    row.append(result.get(header, ''))
            
            writer.writerow(row)
        
        writer.writerow([])  # Empty row separator
        return output.getvalue()
    
    def _create_ai_insights_csv(self, insights: Dict[str, Any]) -> str:
        """Create CSV for AI insights"""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter, quotechar=self.quotechar)
        
        writer.writerow(['AI INSIGHTS'])
        writer.writerow(['Insight Type', 'Key Metric', 'Value', 'Recommendation'])
        
        for insight_type, insight_data in insights.items():
            if isinstance(insight_data, dict):
                # Extract key metrics
                for key, value in insight_data.items():
                    if key == 'recommendation':
                        continue
                    writer.writerow([
                        insight_type.replace('_', ' ').title(),
                        key.replace('_', ' ').title(),
                        str(value),
                        insight_data.get('recommendation', '')
                    ])
        
        writer.writerow([])  # Empty row separator
        return output.getvalue()
    
    def _create_performance_csv(self, performance: Dict[str, Any]) -> str:
        """Create CSV for performance metrics"""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter, quotechar=self.quotechar)
        
        writer.writerow(['PERFORMANCE METRICS'])
        writer.writerow(['Metric', 'Value', 'Unit'])
        
        for key, value in performance.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    unit = 'ms' if 'time' in sub_key.lower() or 'ms' in sub_key else ''
                    writer.writerow([f"{key} - {sub_key}".replace('_', ' ').title(), str(sub_value), unit])
            else:
                unit = 'ms' if 'time' in key.lower() or 'ms' in key else ('per second' if 'per_second' in key else '')
                writer.writerow([key.replace('_', ' ').title(), str(value), unit])
        
        writer.writerow([])  # Empty row separator
        return output.getvalue()
    
    def _create_recommendations_csv(self, recommendations: List[str]) -> str:
        """Create CSV for recommendations"""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self.delimiter, quotechar=self.quotechar)
        
        writer.writerow(['RECOMMENDATIONS'])
        writer.writerow(['Priority', 'Recommendation'])
        
        for i, recommendation in enumerate(recommendations, 1):
            priority = 'High' if i <= 3 else ('Medium' if i <= 6 else 'Low')
            writer.writerow([priority, recommendation])
        
        writer.writerow([])  # Empty row separator
        return output.getvalue()
    
    def _combine_csv_sections(self, sections: Dict[str, str]) -> str:
        """Combine all CSV sections into single file"""
        combined = []
        
        # Add header
        combined.append(f"Enhanced Trade Reconciliation Report")
        combined.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        combined.append("")
        
        # Add each section
        for section_name, section_content in sections.items():
            combined.append(section_content)
        
        return '\n'.join(combined)


class PDFExporter:
    """Export reports to PDF format with formatting and charts"""
    
    def __init__(self):
        self.page_size = 'A4'
        self.font_size = 10
        self.title_font_size = 16
        self.header_font_size = 12
    
    def export(self, report_data: Dict[str, Any], output_path: Optional[str] = None) -> Union[str, bytes]:
        """
        Export report to PDF format.
        
        Note: This is a simplified implementation. In production, you would use
        libraries like reportlab, weasyprint, or similar for proper PDF generation.
        
        Args:
            report_data: Report data dictionary
            output_path: Optional file path to save to
            
        Returns:
            HTML string (simplified) or bytes if saved to file
        """
        try:
            # Generate HTML content that can be converted to PDF
            html_content = self._generate_html_report(report_data)
            
            if output_path:
                # In production, convert HTML to PDF using appropriate library
                with open(output_path.replace('.pdf', '.html'), 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"PDF report (as HTML) exported to {output_path}")
                return html_content.encode('utf-8')
            
            return html_content
            
        except Exception as e:
            logger.error(f"Failed to export PDF report: {e}")
            raise
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content for PDF conversion"""
        html_parts = []
        
        # HTML header
        html_parts.append("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Enhanced Trade Reconciliation Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }
                .section { margin: 20px 0; }
                .section-title { font-size: 14px; font-weight: bold; color: #333; border-bottom: 1px solid #ccc; }
                .summary-table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                .summary-table th, .summary-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                .summary-table th { background-color: #f2f2f2; }
                .recommendation { background-color: #f9f9f9; padding: 10px; margin: 5px 0; border-left: 4px solid #007bff; }
                .chart-placeholder { background-color: #f0f0f0; padding: 20px; text-align: center; margin: 10px 0; }
                .status-matched { color: #28a745; font-weight: bold; }
                .status-mismatched { color: #dc3545; font-weight: bold; }
                .status-partial { color: #ffc107; font-weight: bold; }
            </style>
        </head>
        <body>
        """)
        
        # Report header
        html_parts.append(f"""
        <div class="header">
            <h1>Enhanced Trade Reconciliation Report</h1>
            <p>Report ID: {report_data.get('report_id', 'N/A')}</p>
            <p>Generated: {report_data.get('generation_timestamp', datetime.now().isoformat())}</p>
        </div>
        """)
        
        # Executive summary
        html_parts.append(self._generate_summary_html(report_data.get('processing_summary', {})))
        
        # AI insights
        if report_data.get('ai_insights'):
            html_parts.append(self._generate_ai_insights_html(report_data['ai_insights']))
        
        # Performance metrics
        html_parts.append(self._generate_performance_html(report_data.get('performance_metrics', {})))
        
        # Visualizations
        if report_data.get('visualization_data'):
            html_parts.append(self._generate_visualizations_html(report_data['visualization_data']))
        
        # Recommendations
        html_parts.append(self._generate_recommendations_html(report_data.get('recommendations', [])))
        
        # Detailed results (summary only for PDF)
        html_parts.append(self._generate_detailed_results_summary_html(report_data.get('detailed_results', [])))
        
        # HTML footer
        html_parts.append("""
        </body>
        </html>
        """)
        
        return ''.join(html_parts)
    
    def _generate_summary_html(self, summary: Dict[str, Any]) -> str:
        """Generate HTML for processing summary"""
        html = ['<div class="section">']
        html.append('<h2 class="section-title">Executive Summary</h2>')
        html.append('<table class="summary-table">')
        
        for key, value in summary.items():
            if isinstance(value, dict):
                html.append(f'<tr><th colspan="2">{key.replace("_", " ").title()}</th></tr>')
                for sub_key, sub_value in value.items():
                    html.append(f'<tr><td>&nbsp;&nbsp;{sub_key.replace("_", " ").title()}</td><td>{sub_value}</td></tr>')
            else:
                formatted_value = f"{value:.2f}%" if "rate" in key.lower() and isinstance(value, (int, float)) else str(value)
                html.append(f'<tr><td>{key.replace("_", " ").title()}</td><td>{formatted_value}</td></tr>')
        
        html.append('</table>')
        html.append('</div>')
        return ''.join(html)
    
    def _generate_ai_insights_html(self, insights: Dict[str, Any]) -> str:
        """Generate HTML for AI insights"""
        html = ['<div class="section">']
        html.append('<h2 class="section-title">AI Insights</h2>')
        
        for insight_type, insight_data in insights.items():
            if isinstance(insight_data, dict):
                html.append(f'<h3>{insight_type.replace("_", " ").title()}</h3>')
                html.append('<ul>')
                for key, value in insight_data.items():
                    if key != 'recommendation':
                        html.append(f'<li><strong>{key.replace("_", " ").title()}:</strong> {value}</li>')
                html.append('</ul>')
                
                if 'recommendation' in insight_data:
                    html.append(f'<div class="recommendation">{insight_data["recommendation"]}</div>')
        
        html.append('</div>')
        return ''.join(html)
    
    def _generate_performance_html(self, performance: Dict[str, Any]) -> str:
        """Generate HTML for performance metrics"""
        html = ['<div class="section">']
        html.append('<h2 class="section-title">Performance Metrics</h2>')
        html.append('<table class="summary-table">')
        
        for key, value in performance.items():
            if isinstance(value, dict):
                html.append(f'<tr><th colspan="2">{key.replace("_", " ").title()}</th></tr>')
                for sub_key, sub_value in value.items():
                    unit = ' ms' if 'time' in sub_key.lower() or 'ms' in sub_key else ''
                    html.append(f'<tr><td>&nbsp;&nbsp;{sub_key.replace("_", " ").title()}</td><td>{sub_value}{unit}</td></tr>')
            else:
                unit = ' ms' if 'time' in key.lower() or 'ms' in key else (' per second' if 'per_second' in key else '')
                html.append(f'<tr><td>{key.replace("_", " ").title()}</td><td>{value}{unit}</td></tr>')
        
        html.append('</table>')
        html.append('</div>')
        return ''.join(html)
    
    def _generate_visualizations_html(self, viz_data: Dict[str, Any]) -> str:
        """Generate HTML for visualizations (placeholders)"""
        html = ['<div class="section">']
        html.append('<h2 class="section-title">Visualizations</h2>')
        
        for chart_name, chart_data in viz_data.items():
            if isinstance(chart_data, dict) and 'title' in chart_data:
                html.append(f'<h3>{chart_data["title"]}</h3>')
                html.append(f'<div class="chart-placeholder">Chart: {chart_name.replace("_", " ").title()}<br>')
                html.append(f'Type: {chart_data.get("type", "unknown")}<br>')
                html.append('(Chart visualization would be rendered here in production)</div>')
        
        html.append('</div>')
        return ''.join(html)
    
    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """Generate HTML for recommendations"""
        html = ['<div class="section">']
        html.append('<h2 class="section-title">Recommendations</h2>')
        
        for i, recommendation in enumerate(recommendations, 1):
            priority = 'High' if i <= 3 else ('Medium' if i <= 6 else 'Low')
            html.append(f'<div class="recommendation"><strong>Priority {priority}:</strong> {recommendation}</div>')
        
        html.append('</div>')
        return ''.join(html)
    
    def _generate_detailed_results_summary_html(self, results: List[Dict[str, Any]]) -> str:
        """Generate HTML summary of detailed results"""
        html = ['<div class="section">']
        html.append('<h2 class="section-title">Detailed Results Summary</h2>')
        
        if not results:
            html.append('<p>No detailed results available.</p>')
        else:
            html.append(f'<p>Total trades processed: {len(results)}</p>')
            
            # Status breakdown
            status_counts = {}
            for result in results:
                status = result.get('overall_status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            html.append('<h3>Status Breakdown:</h3>')
            html.append('<ul>')
            for status, count in status_counts.items():
                css_class = f"status-{status.lower().replace('_', '-')}"
                html.append(f'<li class="{css_class}">{status.replace("_", " ").title()}: {count}</li>')
            html.append('</ul>')
            
            html.append('<p><em>For complete detailed results, please refer to the CSV or JSON export.</em></p>')
        
        html.append('</div>')
        return ''.join(html)


class ReportExportManager:
    """Manages export of reports to multiple formats"""
    
    def __init__(self):
        self.exporters = {
            'json': JSONExporter(),
            'csv': CSVExporter(),
            'pdf': PDFExporter()
        }
    
    def export_report(self, report_data: Dict[str, Any], formats: List[str], 
                     output_dir: Optional[str] = None) -> Dict[str, Union[str, bytes]]:
        """
        Export report to multiple formats.
        
        Args:
            report_data: Report data dictionary
            formats: List of formats to export to
            output_dir: Optional output directory
            
        Returns:
            Dictionary mapping format to exported content
        """
        results = {}
        
        report_id = report_data.get('report_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for format_name in formats:
            if format_name not in self.exporters:
                logger.warning(f"Unsupported export format: {format_name}")
                continue
            
            try:
                exporter = self.exporters[format_name]
                
                if output_dir:
                    output_path = Path(output_dir) / f"reconciliation_report_{report_id}_{timestamp}.{format_name}"
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    results[format_name] = exporter.export(report_data, str(output_path))
                else:
                    results[format_name] = exporter.export(report_data)
                
                logger.info(f"Successfully exported report to {format_name} format")
                
            except Exception as e:
                logger.error(f"Failed to export report to {format_name}: {e}")
                results[format_name] = f"Export failed: {e}"
        
        return results