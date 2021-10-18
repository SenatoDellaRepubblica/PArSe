

from engine.misc.misc import run_command


def tika_convert(filename_to_convert):
    """
    Converte un file in puro testo UTF-8
    
    :param filename_to_convert: 
    :return: 
    """
    jar = "./bin/tika/tika-app-1.14.jar"
    command = f"java -jar {jar} --text --encoding=UTF-8 \"{filename_to_convert}\""
    # command = "java -jar {0} --text \"{1}\"".format(jar, filename_to_convert)
    ret = run_command(command)
    output_text = str(ret.stdout, 'utf-8')
    error = str(ret.stderr, 'utf-8')
    return output_text, error
