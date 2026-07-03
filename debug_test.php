<?php

require "/root/wiki-engine-blueprint/php/vendor/autoload.php";

use MintWiki\Document\Document;
use MintWiki\Document\DuplicateNormalizedTitleError;
use MintWiki\Document\Repository;
use MintWiki\Document\Service;
use MintWiki\Http\DocumentCreateHandler;
use MintWiki\Ui\DocumentViewPage;

$repo = new class implements Repository {
    private $docs = [];
    private $titleMap = [];

    public function create(Document $document): Document
    {
        echo "Creating document with title: " . $document->title() . ", normalized: " . $document->normalizedTitle() . "\n";
        echo "Current documents: " . count($this->docs) . "\n";

        foreach ($this->docs as $existing) {
            echo "  Checking existing: " . $existing->normalizedTitle() . "\n";
            if ($existing->normalizedTitle() === $document->normalizedTitle()) {
                echo "  DUPLICATE FOUND!\n";
                throw new DuplicateNormalizedTitleError();
            }
        }

        echo "  No duplicate found, storing document\n";
        $this->docs[$document->id()] = $document;
        $this->titleMap[$document->normalizedTitle()] = $document->id();
        echo "  Stored. Total documents now: " . count($this->docs) . "\n";
        return $document;
    }

    public function get(string $id): ?Document
    {
        return $this->docs[$id] ?? null;
    }

    public function getByNormalizedTitle(string $normalizedTitle): ?Document
    {
        $id = $this->titleMap[$normalizedTitle] ?? null;
        return $id ? ($this->docs[$id] ?? null) : null;
    }

    public function update(Document $document): Document
    {
        $this->docs[$document->id()] = $document;
        return $document;
    }
};

$service = new Service($repo);
$handler = new DocumentCreateHandler($service, new DocumentViewPage());

echo "=== First creation ===\n";
$r1 = $handler->handle("Test Title");
echo "Status: " . $r1->status() . "\n\n";

echo "=== Second creation (should fail) ===\n";
$r2 = $handler->handle("Test Title");
echo "Status: " . $r2->status() . "\n";
echo "Contains error: " . (str_contains($r2->body(), "이미 존재하는 제목입니다") ? "yes" : "no") . "\n";
