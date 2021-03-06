from lightwood.api.types import LightwoodConfig


def call(entity: dict, lightwood_config: LightwoodConfig) -> str:
    dynamic_args = [f'{k}={v}' for k, v in entity['dynamic_args'].items()]

    config_args = []
    for k, v in entity['config_args'].items():
        val = lightwood_config
        for item in v.split('.'):
            val = val.__getattribute__(item)
        config_args.append(f'{k}={val}')

    args = ', '.join(config_args + dynamic_args)

    call = entity['object']

    return f'{call}({args})'


def inline_dict(obj: dict) -> str:
    arr = []
    for k, v in obj.items():
        arr.append(f"""'{k}': {v}""")

    dict_code = '{\n' + ',\n'.join(arr) + '\n}'
    return dict_code


def align(code: str, indent: int) -> str:
    add_space = ''
    for _ in range(indent):
        add_space += '    '

    code_arr = code.split('\n')
    code = f'\n{add_space}'.join(code_arr)
    return code