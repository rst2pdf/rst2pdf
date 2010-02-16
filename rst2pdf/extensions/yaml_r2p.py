''' Wire in a yaml parser for stylesheets.
'''
import yaml
import rst2pdf.styles as styles

styles.json_loads = yaml.load
