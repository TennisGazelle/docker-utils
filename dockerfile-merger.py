#!/usr/local/bin/python3
import logging
import json
import docker
from docker.models.images import Image
import argparse

logging.basicConfig(level=logging.INFO)
pulled_images = []
docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')


class DockerImage:
    image: Image()

    def __init__(self, package_name):
        self.package_name = package_name
        self.cmds = []
        self.special_binaries = {
            "ADD": [],
            "CMD": [],
            "COPY": [],
            "ENTRYPOINT": [],
            "ARG": [],
            "ENV": [],
            "UNKNOWN": []
        }
        self.identify_image()
        self.get_image_history()

    def identify_image(self):
        images = []
        for image in docker_client.images.list(all=True):
            for tag in image.tags:
                if self.package_name in tag:
                    images.append(image)
                    break

        if images.__len__() > 1:
            logging.error("multiple images found for tag {}, please specify a specific one".format(self.package_name))
            for image in images:
                logging.error(
                    "{} with tags \n\t- {}".format(image.id, "\n\t- ".join(docker_client.images.get(image.id).tags)))
        elif images.__len__() == 0:
            logging.warning("no image found with tag {}, pulling...".format(self.package_name))
            docker_client.images.pull(repository='dockerhub.com', tag=self.package_name)
            # todo: add fail conditions here
            pulled_images.append(self.package_name)
        else:
            # we have exactly one
            self.image = images[0]
            logging.info("{} image found: {}".format(self.package_name, self.image.id))

    def get_image_history(self):
        history_lines = docker_client.images.get(self.image.id).history()
        for index, line in enumerate(reversed(history_lines)):
            trimmed_line = line['CreatedBy'].replace("/bin/sh -c", "").replace("#(nop)", "").lstrip()

            # categorize all cmds for later checking
            categorized = False
            for key in self.special_binaries.keys():
                if trimmed_line[0:len(key)] == key:
                    self.special_binaries[key].append({'line': trimmed_line, 'line_number': index})
                    categorized = True
            if not categorized:
                self.special_binaries['UNKNOWN'].append({'line': trimmed_line, 'line_number': index})

            self.cmds.append(trimmed_line)
            logging.debug(trimmed_line)

        logging.debug(json.dumps(self.special_binaries, indent=3))

    def flatten_cmds(self, specific_cmd):
        return [add_cmd['line'] for add_cmd in self.special_binaries[specific_cmd]]

    def print_add_cmds(self):
        logging.info("{}: \n\t- {}".format(self.package_name, "\n\t- ".join(self.flatten_cmds('ADD'))))

    def is_compatible_with(self, other_docker_image):
        assert isinstance(other_docker_image, DockerImage)
        logging.info("comparing the ADD cmds for docker images: {} and {}".format(self.package_name,
                                                                                  other_docker_image.package_name))
        self.print_add_cmds()
        other_docker_image.print_add_cmds()
        return self.flatten_cmds('ADD') == other_docker_image.flatten_cmds('ADD')

    def has_no_copies(self):
        return self.flatten_cmds('COPY').__len__() == 0

    def extend_from(self, base_image):
        assert isinstance(base_image, DockerImage)
        if not self.has_no_copies():
            if self.flatten_cmds('COPY') == base_image.flatten_cmds('COPY'):
                pass
            else:
                logging.error('image {} has copy commands, aborting...'.format(self.package_name))
                return
        elif not self.is_compatible_with(base_image):
            logging.error(
                'images {} and {} are non compatible (different base ADD cmds), aborting...'.format(self.package_name,
                                                                                                    base_image.package_name))
            return

        # merging the other with myself
        final_cmds = []
        cmds_to_skip = self.flatten_cmds('ADD') + self.flatten_cmds('CMD') + self.flatten_cmds('COPY') + \
                       self.flatten_cmds('ENTRYPOINT')

        final_cmds.append('FROM {}'.format(base_image.package_name))
        for cmd in self.cmds:
            if cmd in cmds_to_skip:
                continue
            elif cmd in self.flatten_cmds('UNKNOWN'):
                cmd = 'RUN {}'.format(cmd)
            final_cmds.append(cmd)

        return final_cmds


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Produce Dockerfile that merges two docker base images')
    parser.add_argument('images', metavar='i', type=str, nargs=2, help='images to merge')
    parser.add_argument('-c', '--check-compatibility', help='print out the base ADD cmd of each image', action='store_true')
    args = parser.parse_args()
    lhs = DockerImage(args.images[0])
    rhs = DockerImage(args.images[1])

    if args.check_compatibility:
        print(lhs.is_compatible_with(rhs))
    else:
        with open('Dockerfile.{}.{}'.format(lhs.package_name, rhs.package_name), 'w+') as f:
            f.write("\n".join(rhs.extend_from(lhs)))
