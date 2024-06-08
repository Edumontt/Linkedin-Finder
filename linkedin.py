#!/usr/bin/python3

import argparse
import re
import requests
import csv

def conf_parameters():
    parser = argparse.ArgumentParser(description='Enumerate people and companies from LinkedIn by communicating directly with the API via the CLI.')
    parser.add_argument('-s', '--search', type=str, choices=['profile', 'company'], default='profile', help='Search for profile (company search available in the future)')
    parser.add_argument('-l', '--li-at', type=str, help='Set the li_at Session Cookie of LinkedIn Cookies', required=True)
    parser.add_argument('-t', '--targets', type=argparse.FileType('r'), help='Input file with profile/company (csv/list)', required=True)
    parser.add_argument('-o', '--output', type=argparse.FileType('w'), help='Output file for search results')
    parser.add_argument('-f', '--format', type=str, choices=['txt', 'csv'], default='txt', help='Output file format')

    return parser

def parse_input(args):
    lines = args.targets.readlines()
    targets = []
    targets_ = []
    for line in lines:
        if (args.search == "profile"):
            targets += re.findall("\/in\/[a-zA-Z0-9_\.-]*?\/", line)

    for target in targets:
        target_ = target.split("/")[2]
        targets_.append(target_)

    return list(set(targets_))

def profile_lookup(profile, li_at):
    profile_url = "https://www.linkedin.com/voyager/api/identity/dash/profiles?q=memberIdentity&memberIdentity={}&decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfileWithEntities-35".format(profile)

    headers = {'Csrf-Token': 'linkedin-finder', 'X-RestLi-Protocol-Version': '2.0.0'}
    cookies = {'JSESSIONID': 'linkedin-finder', 'li_at': li_at }

    try:
        profile_response = requests.get(profile_url, cookies=cookies, headers=headers, allow_redirects=True)
        profile_response.raise_for_status()
        profile_data = profile_response.json()

        if 'elements' in profile_data and profile_data['elements']:
            data_nome = profile_data['elements'][0].get('firstName', 'Sem nome')
            data_sobrenome = profile_data['elements'][0].get('lastName', 'Sem sobrenome')
            data_descricao = profile_data['elements'][0].get('headline', 'Sem descrição')
            data_local = profile_data['elements'][0].get('locationName', 'Sem localização')

            data_companies = []
            data_schools = []

            if 'profilePositionGroups' in profile_data['elements'][0]:
                data_companies = ["Empresa: {}, Título: {}, Período: {} - {}".format(
                    d.get('companyName', 'N/A'),
                    d.get('title', 'N/A'),
                    d.get('timePeriod', {}).get('startDate', {}).get('year', 'N/A'),
                    d.get('timePeriod', {}).get('endDate', {}).get('year', 'N/A')
                ) for d in profile_data['elements'][0]['profilePositionGroups']['elements']]

            if 'profileEducations' in profile_data['elements'][0]:
                data_schools = ["Escola: {}, Grau: {}, Área de estudo: {}, Período: {} - {}".format(
                    d.get('schoolName'),
                    d.get('degreeName'),
                    d.get('fieldOfStudy'),
                    d.get('timePeriod', {}).get('startDate', {}).get('year'),
                    d.get('timePeriod', {}).get('endDate', {}).get('year')
                ) for d in profile_data['elements'][0]['profileEducations']['elements']]

            data_profile_url = profile_data['elements'][0].get('publicIdentifier')
            data_summary = profile_data['elements'][0].get('summary', 'N/A')

            return {
                'first_name': data_nome,
                'last_name': data_sobrenome,
                'headline': data_descricao,
                'location': data_local,
                'profile_url': "https://www.linkedin.com/in/{}".format(data_profile_url),
                'companies': " | ".join(data_companies),
                'schools': " | ".join(data_schools),
                'summary': data_summary.replace('\n', ' ')
            }
        else:
            return None
    except requests.exceptions.RequestException as e:
        print("Error fetching profile:", e)
        return None

if __name__ == "__main__":
    parser = conf_parameters()
    args = parser.parse_args()
    targets = parse_input(args)
    results = []
    output = ""

    if (args.search == "profile"):
        
        if (args.format == "csv"):
           output += "first_name,last_name,headline,location,profile_url,companies,schools,summary\n"

        for target in targets:
            profile_data = profile_lookup(target, args.li_at)
            if profile_data:
                results.append(profile_data)
            
            if (args.format == "txt"):
                output += "\nPerfil encontrado:"
                output += f"\nNome: {profile_data['first_name']} {profile_data['last_name']}"
                output += f"\nDescrição: {profile_data['headline']}"
                output += f"\nLocalização: {profile_data['location']}"
                output += f"\nURL do perfil: {profile_data['profile_url']}"
                output += "\n\nExperiências Profissionais:"
                output += f"\n{profile_data['companies']}"
                output += "\n\nEducação:"
                output += f"\n{profile_data['schools']}"
                output += "\n\nResumo:"
                output += f"\n{profile_data['summary']}"
                output += "\n\n======================================\n"

            if (args.format == "csv"):
                for result in results:
                    output += f"\"{result['first_name']}\",\"{result['last_name']}\",\"{result['headline']}\",\"{result['location']}\",\"{result['profile_url']}\",\"{result['companies']}\",\"{result['schools']}\",\"{result['summary']}\"\n"

    if args.output:
        args.output.write(output)
        args.output.close()
    else:
        print(output)

