"""Translate file names to the appropriate targets."""

import logging
import os
import subprocess
from shutil import rmtree

from dfm.mappings import DEFAULT_MAPPINGS, Mapping
from dfm.config import home_dir

logger = logging.getLogger(__name__)


def unable_to_remove(filename, overwrite=False):
    """Remove the file if necessary. If unable to remove for some reason return True."""
    if os.path.islink(filename):
        os.remove(filename)
        return False

    # Doesn't exist
    if not (os.path.isdir(filename) or os.path.isfile(filename)):
        return False

    if not overwrite:
        logger.warning(
            "%s exists and is not a symlink, Cowardly refusing to remove.",
            filename,
        )
        return True

    if os.path.isdir(filename):
        rmtree(filename)
    else:
        os.remove(filename)

    return False


class LinkManager:
    """
    Manages symlinks to a dotfile repository.

    This class handles all linking of a dotfile repository. It should not normally be
    used directly and instead Profile should be used.
    """

    def __init__(
        self,
        where,
        target_dir=None,
        mappings=None,
    ):
        self.where = where
        if target_dir is None:
            self.target_dir = home_dir()
        else:
            self.target_dir = target_dir
        if mappings is None:
            self.mappings = DEFAULT_MAPPINGS
        else:
            self.mappings = mappings

    @classmethod
    def from_config(cls, where, config):
        """Load link manager settings from config."""
        return cls(
            where=where,
            target_dir=config.pop("target_dir", home_dir()),
            mappings=Mapping.from_config(config),
        )

    def link(self, dry_run=False, overwrite=False):
        """
        Link this profile to self.target_dir

        If the destination of a link is missing intervening
        directories this function will attempt to create them.
        """
        for link in self.generate_links():
            if unable_to_remove(link["dst"], overwrite=overwrite):
                continue

            logger.info("Linking %s to %s", link["src"], link["dst"])
            if dry_run:
                continue

            os.makedirs(os.path.dirname(link["dst"]), exist_ok=True)
            os.symlink(**link)

    def translate_name(self, filename):
        """Dotfile-ifies a filename."""
        # Get the absolute path to src
        src = os.path.abspath(filename)
        dest = src.replace(self.where, "")

        # self.where does not always contain a trailing slash
        # This removes a leading slash from the front of dest if where
        # does not contain the trailing slash.
        if dest.startswith(os.sep):
            dest = dest[1:]

        dest = os.path.join(self.target_dir, dest)
        return (src, dest)

    def generate_link(self, filename):
        """Generate link args for filename.
        In case of multiple matches,
        only the last one is actually considered."""
        src, dest = self.translate_name(filename)

        file_should_skip = False
        for mapping in self.mappings:
            # If the mapping doesn't match
            # then check the next one
            if not mapping.matches(filename):
                continue
            # If it does match, it is a higher-priority mapping
            # and replaces the previous one.
            file_should_skip = False

            # If the mapping is a skip mapping
            # then check the next one
            # and skip this file if there are no others.
            if mapping.should_skip():
                file_should_skip = True
                continue

            if mapping.link_as_dir:
                src, dest = self.translate_name(mapping.src_path(self.where))
            else:
                dest = mapping.replace(dest, self.target_dir)
        if file_should_skip:
            return None
        else:
            return {"src": src, "dst": dest}

    def find_files(self):
        """Load the files in this dotfile repository."""
        proc = subprocess.run(
            [
                "git",
                "ls-files",
                "--others",
                "--cached",
                "--exclude-standard",
            ],
            cwd=self.where,
            check=True,
            capture_output=True,
        )
        return [
            os.path.join(self.where, f)
            for f in proc.stdout.decode("utf-8").split("\n")
            if f.strip()
        ]

    def generate_links(self):
        """
        Generate a list of kwargs for os.link.

        All required arguments for os.link will always be provided and
        optional arguments as required.
        """
        return map(
            dict,
            # When using link_as_dir it's possible to have duplicate link
            # directives, this filters those out using a set comprehension.
            {
                tuple(sorted(link.items()))
                for link in map(
                    self.generate_link,
                    self.find_files(),
                )
                if link is not None
            },
        )
