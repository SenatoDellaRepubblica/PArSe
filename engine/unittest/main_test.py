from engine.misc.misc import pretty_print_xml

if __name__ == '__main__':
    xml = """
    <doc>pippo "pluto"</doc>
    """
    new_xml = pretty_print_xml(xml)
    print(new_xml)